from typing import TypedDict


class Drone(TypedDict):
    name: str
    speed: float
    battery: int
    position: dict
    timestamp: int
    isOn: bool
