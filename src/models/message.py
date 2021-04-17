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
        'returnToBase',
        'mission',
        'missionPulse',
        'stopMission',
        'loadProject',
        'loadProjectLog'
    ]
    data: dict
