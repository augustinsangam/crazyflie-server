from typing import TypedDict, Literal, List, Optional, Dict


class Vec2(TypedDict):
    x: float
    y: float


class MissionPoint(TypedDict):
    droneName: str
    value: Vec2


MissionDrones = Dict[str, str]
MissionDronesPositions = Dict[str, Vec2]
MissionStatus = Literal['requested', 'rejected', 'inProgress', 'failed', 'done']
MissionType = Literal['fake', 'argos', 'crazyradio']
MissionDronesPaths = Dict[str, List[Vec2]]


class Mission(TypedDict):
    id: str
    status: MissionStatus
    timestamp: int
    type: MissionType
    drones: MissionDrones
    dronesPositions: MissionDronesPositions
    dronesPaths: MissionDronesPaths
    shapes: List[List[Vec2]]
    points: List[MissionPoint]


class MissionPulse(Mission, total=False):
    pass
