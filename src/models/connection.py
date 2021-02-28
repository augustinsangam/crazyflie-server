from collections import defaultdict
from enum import Enum
from typing import Callable, Dict, TypedDict, Tuple


class HandlerType(Enum):
    connection = 'connection'
    disconnection = 'disconnection'
    message = 'message'
    error = 'error'


class Handler(TypedDict):
    callback: Callable
    args: Tuple
    kwargs: Dict


class Connection:

    def __init__(self) -> None:
        self.handlers = defaultdict(list)

    def addCallback(self, handlerType: HandlerType, callback: Callable, *args, **kwargs) -> None:
        handler = Handler(
            callback=callback,
            args=args,
            kwargs=kwargs
        )
        self.handlers[handlerType].append(handler)

    def removeCallback(self, handlerType: HandlerType, callback: Callable) -> None:
        if handlerType not in self.handlers:
            return

        def filterFunc(handler: Handler) -> bool:
            return handler['callback'] == callback

        self.handlers[handlerType] = list(filter(filterFunc, self.handlers[handlerType]))

    def callAllCallbacks(self, handlerType: HandlerType, *args, **kwargs) -> None:
        handler: Handler
        for handler in self.handlers[handlerType]:
            callback = handler['callback']
            callbackArgs = (*args, *handler['args'])
            callbackKwargs = {**handler['kwargs'], **kwargs}
            callback(*callbackArgs, **callbackKwargs)
