from typing import List, Literal, TypedDict

DroneState = Literal["onTheGround", "takingOff", "landing", "crashed",
                     "exploring", "standBy", "returningToBase"]


class Drone(TypedDict):
    name: str
    timestamp: int
    speed: float
    battery: float
    position: List[float]
    yaw: float
    ranges: List[int]
    timestamp: int
    state: DroneState
    ledOn: bool
    real: bool


def droneDiff(oldDrone: Drone, newDrone: Drone) -> dict:
    diff = {}
    for oldAttribute in oldDrone:
        if oldDrone[oldAttribute] != newDrone[oldAttribute]:  # noqa
            diff[oldAttribute] = newDrone[oldAttribute]  # noqa
    diff['name'] = newDrone['name']
    diff['timestamp'] = newDrone['timestamp']
    return diff
