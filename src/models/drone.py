from typing import List, TypedDict


class Drone(TypedDict):
    name: str
    speed: float
    battery: float
    position: List[float]
    orientation: float
    multiRange: List[int]
    timestamp: int
    flying: bool
    ledOn: bool
    real: bool
