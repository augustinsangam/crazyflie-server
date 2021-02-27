import logging
from collections import defaultdict
from enum import Enum
from typing import Callable, Dict, List, TypedDict


class HandlerType(Enum):
    connection = 'connection'
    disconnection = 'disconnection'
    message = 'message'
    error = 'error'


class Handler(TypedDict):
    callback: Callable
    args: List
    kwargs: Dict


class Connection:

    def __init__(self) -> None:
        self.handlers = defaultdict(list)

    def addCallback(self, type: HandlerType, callback: Callable, *args, **kwargs) -> None:
        handler: Handler = {
            "callback": callback,
            "args": args,
            "kwargs": kwargs
        }
        self.handlers[type].append(handler)

    def removeCallback(self, type: HandlerType, callback: Callable) -> None:
        if type not in self.handlers:
            return

        def filterFunc(handler: Handler) -> bool:
            return handler['callback'] == callback

        self.handlers[type] = list(filter(filterFunc, self.handler[type]))

    def callAllCallbacks(self, type: HandlerType, *args, **kwargs) -> None:
        handler: Handler
        for handler in self.handlers[type]:
            callback = handler['callback']
            callbackArgs = (*args, *handler['args'])
            callbackKwargs = {**handler['kwargs'], **kwargs}
            callback(*callbackArgs, **callbackKwargs)
