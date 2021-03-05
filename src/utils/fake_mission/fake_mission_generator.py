import json
import pathlib
from io import StringIO
from typing import List, Tuple, TypedDict


class Vec2(TypedDict):
    x: float
    y: float


def findNextMove(mission: List, pos: Vec2, lastPos: Vec2) -> Tuple:
    if mission[int(pos['y']+1)][int(pos['x'])] == '*' and Vec2(y=pos['y']+1, x=pos['x']) != lastPos:
        return False, Vec2(y=pos['y']+1, x=pos['x'])
    elif mission[int(pos['y']-1)][int(pos['x'])] == '*' and Vec2(y=pos['y']-1, x=pos['x']) != lastPos:
        return False, Vec2(y=pos['y']-1, x=pos['x'])
    elif mission[int(pos['y'])][int(pos['x']+1)] == '*' and Vec2(y=pos['y'], x=pos['x']+1) != lastPos:
        return False, Vec2(y=pos['y'], x=pos['x']+1)
    elif mission[int(pos['y'])][int(pos['x']-1)] == '*' and Vec2(y=pos['y'], x=pos['x']-1) != lastPos:
        return False, Vec2(y=pos['y'], x=pos['x']-1)
    else:
        return True, Vec2(x=0, y=0)


def rayCast(mission: List, pos: Vec2, direction: Tuple) -> Vec2:
    y = pos['y']
    x = pos['x']
    for i in range(20):
        if mission[int(y)][int(x)] == '.':
            return Vec2(x=x, y=y)
        x += direction[1]
        y += direction[0]
    return Vec2(x=x, y=y)


def scalePoints(points: List) -> List:
    scaledPoints = []
    for j in range(len(points)):
        scaledPoints.append((points[j]['x']-10.0)/5)
        scaledPoints.append((points[j]['y']-10.0)/5)
    return scaledPoints


def missionPulse(mission: List, droneName: str, pos: Vec2) -> str:
    points = [pos]
    # north
    points.append(rayCast(mission, pos, (-1, 0)))
    # east
    points.append(rayCast(mission, pos, (0, 1)))
    # south
    points.append(rayCast(mission, pos, (1, 0)))
    # west
    points.append(rayCast(mission, pos, (0, -1)))

    scaledPoints = scalePoints(points)

    return f'[\"{droneName}\",[{scaledPoints[0]},{scaledPoints[1]}],[[{scaledPoints[2]},{scaledPoints[3]}],[{scaledPoints[4]},{scaledPoints[5]}],[{scaledPoints[6]},{scaledPoints[7]}],[{scaledPoints[8]},{scaledPoints[9]}]]]'


if __name__ == '__main__':

    fakeMissionFilePath = pathlib.Path(__file__).parent.joinpath(
        'fake_mission.json').absolute().__str__()

    droneFeedFilePath = pathlib.Path(__file__).parent.joinpath(
        'droneFeed.json').absolute().__str__()

    with open(fakeMissionFilePath, 'r') as f:
        jsonMission = json.load(f)

        droneFeedFile = open(droneFeedFilePath, 'wt')

        dronesPos = {}
        dronesLastPos = {}

        for i in range(jsonMission['nb_drone']):
            droneName = f'Drone#{i+1}'
            dronesPos[droneName] = Vec2(
                y=jsonMission[droneName][0], x=jsonMission[droneName][1])

            dronesLastPos[droneName] = Vec2(
                y=jsonMission[droneName][0], x=jsonMission[droneName][1])

        stop = False

        droneFrames = '{"frames":['

        stoppedDrones = []

        while len(stoppedDrones) < jsonMission['nb_drone']:
            for drone in dronesPos:
                if stoppedDrones.__contains__(drone):
                    continue

                pulse = missionPulse(
                    jsonMission['mission'], drone, dronesPos[drone])

                droneFrames += pulse

                tempPos = dronesPos[drone]

                stop, dronesPos[drone] = findNextMove(
                    jsonMission['mission'], dronesPos[drone], dronesLastPos[drone])

                dronesLastPos[drone] = tempPos

                if stop:
                    stoppedDrones.append(drone)

                if len(stoppedDrones) < jsonMission['nb_drone']:
                    droneFrames += ','

        droneFrames += ']}'

        droneFeedFile.write(droneFrames)

        droneFeedFile.close()
