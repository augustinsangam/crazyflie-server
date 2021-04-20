from typing import TypedDict, Literal

MessageType = Literal[
    'pulse',
    'land',
    'takeOff',
    'lighten',
    'darken',
    'disconnect',
    'startMission',
    'returnToBase',
    'mission',
    'missionPulse',
    'stopMission',
    'loadProject',
    'loadProjectLog',
]


class Message(TypedDict):
    type: MessageType
    data: dict
