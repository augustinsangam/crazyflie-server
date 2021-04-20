import logging
import math
from typing import Callable, List, Tuple

import kdtree
from src.models.drone import Drone
from src.models.message import Message
from src.models.mission import (Mission, MissionDrones, MissionPoint,
                                MissionPulse, MissionStatus, MissionType, Vec2)
from src.services.database import DatabaseService
from src.services.drones_set import DronesSet
from src.utils.css_predifined_colors import CSS_PREDEFINED_COLORS
from src.utils.timestamp import getTimestamp




class MissionHandler:
    MAX_DISTANCE = 0.21
    MIN_POINTS_DIST = 0.002
    TAKE_OFF_DELAY = 20
    CRAZYRADIO_MAX_RANGE = 500
    ARGOS_MAX_RANGE = 65530

    def __init__(self, dronesSet: DronesSet, missionType: MissionType, initialDronePos: dict, offsetDronePos: dict,
                 sendMessageCallable: Callable[[Message], None]):
        """Initialize the mission handler. Reject the mission if the droneSet
        is empty. Gives random colors to the drones ins the droneSet. Save
        the newly created mission object and saves it in the database.

          @param dronesSet: the set of drones participating in the mission.
          @param missionType: The type of the mission: real or fake. Fake is
          for demo purposes only. @param sendMessageCallable: the function to
          call to send mission pulses.
        """
        self.RANGE_SCALE: float = (missionType == 'argos') * 0.01 + (missionType == 'crazyradio') * 0.001
        drones: List[Drone] = list(dronesSet.getDrones().values())
        if len(drones) == 0:
            logging.info("Mission rejected: no drones")
            status: MissionStatus = 'rejected'
            sendMessageCallable(
                Message(type='missionPulse', data={'status': status}))
            return
        self.initialDronePos = initialDronePos
        self.offsetDronePos = offsetDronePos
        logging.error(f"Initial {initialDronePos}")
        logging.error(f"Offset {offsetDronePos}")
        self.dronesSet = dronesSet
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
        self.kdtree = kdtree.create(dimensions=2)
        self.maxRange = ((self.mission['type'] == 'argos') * self.ARGOS_MAX_RANGE
                       + (self.mission['type'] == 'crazyradio') * self.CRAZYRADIO_MAX_RANGE)

    def onReceivedPositionAndRange(self, droneName: str, position: Vec2, yaw: float, ranges: List[int]):
        """Calculate the point indicated by the given ranges and orientation.

          @param droneName: the name of the drone witch sent the informations.
          @param position: the 2D position of the drone.
          @param yaw: the angle of the drone in radiant.
          @param ranges: the list of ranges (front, left, back, right)
        """

        realYaw = yaw
        points: List[Vec2] = []

        position['x'] -= self.initialDronePos[droneName]['x']
        position['y'] -= self.initialDronePos[droneName]['y']

        if self.mission['type'] == 'argos':
            xtemp = position['x']
            position['x'] = position['y']
            position['y'] = xtemp
        elif self.mission['type'] == 'crazyradio':
            xtemp = position['x']
            position['x'] = - position['y']
            position['y'] = - xtemp
            realYaw = yaw + math.pi / 4

        xPos = position['x'] + self.offsetDronePos[droneName]['x']
        yPos = position['y'] + self.offsetDronePos[droneName]['y']

        i = 0
        for r in ranges:
            if r > self.maxRange:
                i += 1
                continue
            point = Vec2(
                x=round(r * self.RANGE_SCALE * math.cos(realYaw + i * math.pi / 2)
                        * (-2 * (self.mission['type'] == 'argos') + 1) + xPos, 4),
                y=round(r * self.RANGE_SCALE * math.sin(realYaw + i * math.pi / 2)
                        * (-2 * (self.mission['type'] != 'argos') + 1) + yPos, 4)
            )
            if self.checkPointValidity((point['x'], point['y'])):
                points.append(point)
            i += 1
        self.handlePositionAndBorders(
            droneName, Vec2(x=xPos, y=yPos), points)

    def checkPointValidity(self, point: Tuple[float, float]) -> bool:
        neighbor = self.kdtree.search_nn(point)
        if not neighbor:
            self.kdtree.add(point)
            return True
        if neighbor[1] <= self.MIN_POINTS_DIST:
            return False
        else:
            self.kdtree.add(point)
            return True

    def handlePositionAndBorders(self, droneName: str, position: Vec2, points: List[Vec2]):
        """Add the new position of the drone as well as the position of the border it found to the mission.
        Saves the updated mission to the database.
          @param droneName: the name of the drone witch sent the informations.
          @param position: the 2D position of the drone.
          @param points: a list of 2D points
        """
        newMissionPoints = list(map(lambda point: MissionPoint(
            droneName=droneName, value=point), points))
        missionPulse = MissionPulse(id=self.mission['id'])
        if newMissionPoints:
            missionPulse['points'] = newMissionPoints
        lastPos = self.mission['dronesPositions'][droneName]
        if lastPos == [] or \
                math.dist([lastPos['x'], lastPos['y']], [position['x'], position['y']]) > self.MIN_POINTS_DIST:
            missionPulse['dronesPositions'] = {droneName: position}
            self.mission['dronesPositions'][droneName] = position
            self.mission['dronesPaths'][droneName].append(position)
        self.mission['points'] = [*self.mission['points'], *newMissionPoints]
        DatabaseService.saveMission(self.mission['id'], self.mission)
        if len(missionPulse) > 1:
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

    def recursiveAddPointToShape(self, missionPoints: List[MissionPoint], pointsToAdd: List[MissionPoint],
                                 currentShape: List[Vec2]):
        """Add the points to the current shape, then find the nearest point
        from the given points, sort them by distance, and call this method
        with the newly found points.

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

    def checkMissionEnd(self) -> bool:
        if getTimestamp() - self.mission['timestamp'] < self.TAKE_OFF_DELAY:
            return False
        drone: Drone
        for drone in self.dronesSet.getDrones().values():
            if drone['state'] != 'onTheGround' and drone['state'] != 'crashed':
                return False

        self.endMission()
        return True

    def endMission(self):
        """End the mission. Save the ’done’ status to the database and inform
        the dashboards.
        """
        #self.assignPointsToShapes()
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

    def stopMission(self):
        status: MissionStatus = 'failed'
        missionPulse = MissionPulse(
            id=self.mission['id'],
            status=status,
        ) # noqa
        self.mission['status'] = status
        DatabaseService.saveMission(self.mission['id'], self.mission)
        self.sendMessageCallable(
            Message(type='missionPulse', data=missionPulse))
