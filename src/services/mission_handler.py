from typing import List, Callable

from src.models.drone import Drone
from src.models.message import Message
from src.models.mission import MissionType, MissionStatus, Mission, Vec2, MissionPulse, \
    MissionPoint, MissionDrones
from src.services.drones_set import DronesSet
from src.utils.css_predifined_colors import CSS_PREDEFINED_COLORS
from src.utils.timestamp import getTimestamp


class MissionHandler:

    def __init__(self, dronesSet: DronesSet, missionType: MissionType, sendMessageCallable: Callable[[Message], None]):
        drones: List[Drone] = list(dronesSet.getDrones().values())
        if len(drones) == 0:
            status: MissionStatus = 'rejected'
            sendMessageCallable(Message(type='missionPulse', data={'status': status}))
            return
        self.sendMessageCallable = sendMessageCallable
        missionDrones: MissionDrones = {
            drone['name']: (CSS_PREDEFINED_COLORS[drone['name'].__hash__() % len(CSS_PREDEFINED_COLORS)])
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
        sendMessageCallable(Message(type='missionPulse', data=self.mission))

    def onReceivedPositionAndBorders(self, droneName: str, position: Vec2, points: List[Vec2], ):
        newMissionPoints = list(map(lambda point: MissionPoint(droneName=droneName, value=point), points))
        missionPulse = MissionPulse(
            id=self.mission['id'],
            dronesPositions={droneName: position},
            points=newMissionPoints
        )
        self.mission['dronesPositions'][droneName] = position
        self.mission['dronesPaths'][droneName].append(position)
        self.mission['points'] = [*self.mission['points'], *newMissionPoints]
        self.sendMessageCallable(Message(type='missionPulse', data=missionPulse))
