from collections import defaultdict
from enum import Enum
from typing import Callable, TypedDict, Tuple


class HandlerType(Enum):
    connection = 'connection'
    disconnection = 'disconnection'
    message = 'message'
    error = 'error'


class Handler(TypedDict):
    callback: Callable
    args: Tuple


class Connection:

    def __init__(self) -> None:
        self.handlers = defaultdict(list)

    def addCallback(self, handlerType: HandlerType, callback: Callable, *args) -> None:
        handler = Handler(
            callback=callback,
            args=args
        )
        self.handlers[handlerType].append(handler)

    def removeCallback(self, handlerType: HandlerType, callback: Callable) -> None:
        if handlerType not in self.handlers:
            return

        def filterFunc(handler: Handler) -> bool:
            return handler['callback'] == callback

        self.handlers[handlerType] = list(filter(filterFunc, self.handlers[handlerType]))

    def callAllCallbacks(self, handlerType: HandlerType, *args) -> None:
        handler: Handler
        for handler in self.handlers[handlerType]:
            callback = handler['callback']
            callbackArgs = (*handler['args'], *args)
            callback(*callbackArgs)
