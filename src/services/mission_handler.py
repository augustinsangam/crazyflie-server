import logging
import math
from typing import List, Callable
from src.services.database import DatabaseService

from src.models.drone import Drone
from src.models.message import Message
from src.models.mission import MissionType, MissionStatus, Mission, Vec2, \
    MissionPulse, MissionPoint, MissionDrones
from src.services.drones_set import DronesSet
from src.utils.css_predifined_colors import CSS_PREDEFINED_COLORS
from src.utils.timestamp import getTimestamp


class MissionHandler:
    RANGE_SCALE: float = 0.01
    MAX_DISTANCE = 0.21

    def __init__(self, dronesSet: DronesSet, missionType: MissionType,
                 sendMessageCallable: Callable[[Message], None]):
        """Initialize the mission handler. Reject the mission if the droneSet
        is empty. Gives random colors to the drones ins the droneSet. Save
        the newly created mission object and saves it in the database.

          @param dronesSet: the set of drones participating in the mission.
          @param missionType: The type of the mission: real or fake. Fake is
          for demo purposes only. @param sendMessageCallable: the function to
          call to send mission pulses.
        """
        drones: List[Drone] = list(dronesSet.getDrones().values())
        if len(drones) == 0:
            logging.info("Mission rejected: no drones")
            status: MissionStatus = 'rejected'
            sendMessageCallable(
                Message(type='missionPulse', data={'status': status}))
            return
        self.sendMessageCallable = sendMessageCallable
        missionDrones: MissionDrones = {
            drone['name']: (
                CSS_PREDEFINED_COLORS[
                    drone['name'].__hash__() % len(CSS_PREDEFINED_COLORS)])
            for drone in drones
        }
        timestamp = getTimestamp()
        self.mission = Mission(
            id=f'Mission - {timestamp}',
            timestamp=timestamp,
            type=missionType,
            status='inProgress',
            drones=missionDrones,
            dronesPositions={drone['name']: [] for drone in drones},
            dronesPaths={drone['name']: [] for drone in drones},
            shapes=[],
            points=[]
        )
        DatabaseService.saveMission(self.mission['id'], self.mission)
        sendMessageCallable(Message(type='mission', data=self.mission))

    def onReceivedPositionAndRange(self, droneName: str, position: Vec2,
                                   orientation: float, ranges: List[int]):
        """Calculate the point indicated by the given ranges and orientation.

          @param droneName: the name of the drone witch sent the information.
          @param position: TODO
          @param orientation: the angle of the drone in radiant.
          @param ranges: the list of ranges (front, left, back, right)
        """
        points: List[Vec2] = []
        for i, r in enumerate(ranges):
            if r > 65530:
                continue
            angle = orientation + i * math.pi / 2
            point = Vec2(
                x=r * self.RANGE_SCALE * math.cos(angle) + position['x'],
                y=r * self.RANGE_SCALE * math.sin(angle) + position['y']
            )
            points.append(point)
        self.handlePositionAndBorders(droneName, position, points)

    def handlePositionAndBorders(self, droneName: str, position: Vec2,
                                 points: List[Vec2]):
        """Add the new position of the drone as well as the position of the
        border it found to the mission. Saves the updated mission to the
        database. @param droneName: the name of the drone witch sent the
        information. @param position: the 2D position of the drone. @param
        points: a list of 2D points
        """
        newMissionPoints = list(map(lambda point: MissionPoint(
            droneName=droneName, value=point), points))
        missionPulse = MissionPulse(
            id=self.mission['id'],
            dronesPositions={droneName: position},
            points=newMissionPoints
        )
        self.mission['dronesPositions'][droneName] = position
        self.mission['dronesPaths'][droneName].append(position)
        self.mission['points'] = [*self.mission['points'], *newMissionPoints]
        DatabaseService.saveMission(self.mission['id'], self.mission)
        self.sendMessageCallable(
            Message(type='missionPulse', data=missionPulse))

    def assignPointsToShapes(self):
        """Goes over all the point found during the mission and try to
        regroup them into shapes. Then add the created shape to the current
        mission.
        """
        pointsCopy = self.mission['points'].copy()

        while len(pointsCopy):
            shape = []
            self.recursiveAddPointToShape(pointsCopy, [pointsCopy[0]], shape)
            shape.append(shape[0])
            self.mission['shapes'].append(shape)

    def recursiveAddPointToShape(self, missionPoints: List[MissionPoint],
                                 pointsToAdd: List[MissionPoint],
                                 currentShape: List[Vec2]):
        """Add the points to the current shape, then find the nearest point
        from the given points, sort them by distance, and call this method
        withe the newly found points.

          @param missionPoints: the points witch are not in a shape yet.
          @param currentShape: TODO
          @param pointsToAdd: a list of the points found in the previous
          iteration. @param currentShape: the current shape in witch the
          pointsToAdd will be added.
        """
        for point in pointsToAdd:
            currentShape.append(point['value'])

            nexPointsToAdd = {}
            pointsToRemove = []
            for missionPoint in missionPoints:
                dist = math.dist(
                    [missionPoint['value']['x'], missionPoint['value']['y']], [
                        point['value']['x'], point['value']['y']])
                if dist == 0.0:
                    pointsToRemove.append(missionPoint)
                elif dist <= self.MAX_DISTANCE:
                    nexPointsToAdd[dist] = missionPoint
            for p in list(nexPointsToAdd.values()):
                missionPoints.remove(p)
            for p in pointsToRemove:
                missionPoints.remove(p)

            nexPointsToAdd = dict(
                sorted(nexPointsToAdd.items(), key=lambda i: i[0]))

            if len(nexPointsToAdd):
                self.recursiveAddPointToShape(
                    missionPoints, list(nexPointsToAdd.values()), currentShape)

    def endMission(self):
        """End the mission. Save the ’done’ status to the database and inform
        the dashboards.
        """
        self.assignPointsToShapes()
        status: MissionStatus = 'done'
        missionPulse = MissionPulse(
            id=self.mission['id'],
            status=status,
            shapes=self.mission['shapes']
        )
        self.mission['status'] = status
        DatabaseService.saveMission(self.mission['id'], self.mission)
        self.sendMessageCallable(
            Message(type='missionPulse', data=missionPulse))
