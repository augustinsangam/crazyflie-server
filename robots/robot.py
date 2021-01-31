
from typing import TypedDict

from robots.localization import Localization


class Robot(TypedDict):
    name: str
    speed: float
    batteryPercentage: int
    localization: Localization
    lastUpdate: int
    isOn: bool
