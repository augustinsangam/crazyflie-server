import math
from typing import List, Callable
from services.database import DatabaseService

from src.models.drone import Drone
from src.models.message import Message
from src.models.mission import MissionType, MissionStatus, Mission, Vec2, MissionPulse, \
    MissionPoint, MissionDrones
from src.services.drones_set import DronesSet
from src.utils.css_predifined_colors import CSS_PREDEFINED_COLORS
from src.utils.timestamp import getTimestamp


class MissionHandler:

    RANGE_SCALE: float = 1.0
    MAX_DISTANCE = 0.21

    def __init__(self, dronesSet: DronesSet, missionType: MissionType, sendMessageCallable: Callable[[Message], None]):
        drones: List[Drone] = list(dronesSet.getDrones().values())
        if len(drones) == 0:
            status: MissionStatus = 'rejected'
            sendMessageCallable(
                Message(type='missionPulse', data={'status': status}))
            return
        self.sendMessageCallable = sendMessageCallable
        missionDrones: MissionDrones = {
            drone['name']: (
                CSS_PREDEFINED_COLORS[drone['name'].__hash__() % len(CSS_PREDEFINED_COLORS)])
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

    def onReceivedPositionAndRange(self, droneName: str, position: Vec2, orientation: float, ranges: List[int]):
        points: List[Vec2] = []
        for range in ranges:
            point = Vec2(
                x=range * self.RANGE_SCALE *
                math.cos(orientation) + position['x'],
                y=range * self.RANGE_SCALE *
                math.sin(orientation) + position['y']
            )
            points.append(point)

        self.handlePositionAndBorders(
            self, droneName, position, points)

    def handlePositionAndBorders(self, droneName: str, position: Vec2, points: List[Vec2]):
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

    def onFindShape(self, path: List[Vec2]):
        missionPulse = MissionPulse(
            id=self.mission['id'],
            shapes=[path]
        )
        self.mission['shapes'].append(path)
        DatabaseService.saveMission(self.mission['id'], self.mission)
        self.sendMessageCallable(
            Message(type='missionPulse', data=missionPulse))

    def assingPointsToShapes(self):
        pointsCopy = self.mission['points'].copy()

        while len(pointsCopy):
            shape = []
            self.recusrsiveAddPointToShape(pointsCopy, [pointsCopy[0]], shape)
            shape.append(shape[0])
            self.mission['shapes'].append(shape)

    def recusrsiveAddPointToShape(self, missionPoints: List[MissionPoint], pointsToAdd: List[MissionPoint], currentShape: List[Vec2]):
        for point in pointsToAdd:
            currentShape.append(point['value'])

            nexPointsToAdd = {}
            pointsToRemove = []
            for missionPoint in missionPoints:
                dist = math.dist([missionPoint['value']['x'], missionPoint['value']['y']], [
                    point['value']['x'], point['value']['y']])
                if dist == 0.0:
                    pointsToRemove.append(missionPoint)
                elif dist <= self.MAX_DISTANCE:
                    nexPointsToAdd[dist] = missionPoint
            for point in list(nexPointsToAdd.values()):
                missionPoints.remove(point)
            for point in pointsToRemove:
                missionPoints.remove(point)

            nexPointsToAdd = dict(
                sorted(nexPointsToAdd.items(), key=lambda i: i[0]))

            if len(nexPointsToAdd):
                self.recusrsiveAddPointToShape(
                    missionPoints, list(nexPointsToAdd.values()), currentShape)

    def endMission(self):
        self.assingPointsToShapes()
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
