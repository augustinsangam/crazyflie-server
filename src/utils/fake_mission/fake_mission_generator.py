from io import StringIO
import json
from typing import List, Tuple


def findNextMove(mission: List, pos: Tuple, lastTravel: Tuple) -> Tuple:
    if mission[pos[0]+1][pos[1]] == '*' and (pos[0]+1, pos[1]) != lastTravel:
        return (True, pos[0]+1, pos[1])
    if mission[pos[0]-1][pos[1]] == '*' and (pos[0]-1, pos[1]) != lastTravel:
        return (True, pos[0]-1, pos[1])
    if mission[pos[0]][pos[1]+1] == '*' and (pos[0], pos[1]+1) != lastTravel:
        return (True, pos[0], pos[1]+1)
    if mission[pos[0]][pos[1]-1] == '*' and (pos[0], pos[1]-1) != lastTravel:
        return (True, pos[0], pos[1]-1)
    else:
        return (False, 0, 0)


def rayCast(pos: Tuple, drone: str):

    pass


def missionPulse(drone: str, pos: Tuple) -> bool:

    pass


if __name__ == '__main__':

    missionFile = open('filename.txt', 'r')

    droneFeedFile = open('droneFeed.txt', 'w')

    jsonMission = json.load(StringIO(missionFile.readline()))

    dronesPos = {}

    for i in jsonMission['nb_drone']:
        dronesPos[f'Drone#{i+1}'] = jsonMission[f'Drone#{i+1}']

    stop = False

    while not stop:
        for drone in dronesPos:
            stop = missionPulse()
