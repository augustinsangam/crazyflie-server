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
        """ Add a new handler for the given callback.

          @param handlerType: the type of the handler.
          @param callback: the callback function.
          @param args: the params to give the callback fucntion.
        """
        handler = Handler(
            callback=callback,
            args=args
        )
        self.handlers[handlerType].append(handler)

    def removeCallback(self, handlerType: HandlerType, callback: Callable) -> None:
        """Removes the given callback.

          @param handlerType: the type of the handler
          @param callback:
        """
        if handlerType not in self.handlers:
            return

        def filterFunc(handler: Handler) -> bool:
            return handler['callback'] == callback

        self.handlers[handlerType] = list(filter(filterFunc, self.handlers[handlerType]))

    def callAllCallbacks(self, handlerType: HandlerType, *args) -> None:
        """Call all the registered callbacks of the same type of handler.

          @param handlerType: the type of handler to call the callbacks.
          @param args: the arguments to give to the callback.
        """
        handler: Handler
        for handler in self.handlers[handlerType]:
            callback = handler['callback']
            callbackArgs = (*handler['args'], *args)
            callback(*callbackArgs)
