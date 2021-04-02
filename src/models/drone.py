from typing import List, TypedDict


class Drone(TypedDict):
    name: str
    speed: float
    battery: float
    position: List[float]
    yaw: float
    ranges: List[int]
    timestamp: int
    flying: bool
    ledOn: bool
    real: bool
