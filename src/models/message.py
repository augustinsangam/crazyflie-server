from typing import TypedDict, Literal


class Message(TypedDict):
    type: Literal[
        'pulse',
        'land',
        'takeOff',
        'lighten',
        'darken',
        'disconnect',
        'startMission',
        'mission',
        'missionPulse'
    ]
    data: dict
