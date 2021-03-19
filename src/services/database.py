from typing import List

from src.metaclasses.singleton import Singleton
from src.models.mission import Mission
from tinydb import Query, TinyDB


class DatabaseService(metaclass=Singleton):
    MISSIONS_TABLE_NAME = 'missions'
    db = TinyDB('data/db.json')

    @staticmethod
    def getAllMissions() -> List[Mission]:
        """Return a list of saved mission, sorted by their timestamp.
        """
        table = DatabaseService.db.table(DatabaseService.MISSIONS_TABLE_NAME)
        allMissions: List[Mission] = table.all()
        return sorted(allMissions, key=lambda m: m['timestamp'], reverse=True)

    @staticmethod
    def saveMission(missionId: str, mission: Mission):
        """Save the specified mission into the database. Update the value of the mission id if it already exists.

          @param missionId: the str id of the mission to save/update
          @param mission: the data of the mission to save
        """
        table = DatabaseService.db.table(DatabaseService.MISSIONS_TABLE_NAME)
        missionQuery = Query()
        table.upsert(mission, missionQuery.id == missionId)
