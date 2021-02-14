from typing import List, TypedDict


class Drone(TypedDict):
    name: str
    speed: float
    battery: float
    position: List[float]
    timestamp: int
    flying: bool
    ledOn: bool
    real: bool
