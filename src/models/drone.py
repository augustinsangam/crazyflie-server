from typing import List, TypedDict, Literal

DroneState = Literal["onTheGround", "takingOff", "landing", "crashed",
                     "exploring", "returningToBase"]


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
    for newAttribute in newDrone:
        if newAttribute not in oldDrone:  # noqa
            diff[newAttribute] = newDrone[newAttribute]  # noqa
    diff['name'] = newDrone['name']
    diff['timestamp'] = newDrone['timestamp']
    return diff

