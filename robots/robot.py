
from typing import TypedDict


class Robot(TypedDict):
    name: str
    speed: float
    battery: int
    position: dict
    timestamp: int
    isOn: bool
