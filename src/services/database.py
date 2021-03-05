from typing import List

from src.metaclasses.singleton import Singleton
from tinydb import TinyDB, Query

from src.models.mission import Mission


class DatabaseService(metaclass=Singleton):
    MISSIONS_TABLE_NAME = 'missions'
    db = TinyDB('database/db.json')

    @staticmethod
    def getAllMissions() -> List[Mission]:
        table = DatabaseService.db.table(DatabaseService.MISSIONS_TABLE_NAME)
        return table.all()

    @staticmethod
    def saveMission(missionId: str, mission: Mission):
        table = DatabaseService.db.table(DatabaseService.MISSIONS_TABLE_NAME)
        missionQuery = Query()
        table.upsert(mission, missionQuery.id == missionId)
