from abc import ABC, abstractmethod

from models.message import Message


class Client(ABC):

    @abstractmethod
    def sendMessage(self, message: Message):
        pass
