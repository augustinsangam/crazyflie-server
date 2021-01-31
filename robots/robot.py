
from robots.localization import Localization
from typing import TypedDict


class Robot(TypedDict):
    name: str
    speed: float
    batteryPercentage: int
    localisation: Localization
    lastUpdate: int
    isOn: bool
