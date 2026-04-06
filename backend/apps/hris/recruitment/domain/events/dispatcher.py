from typing import Callable, List, Type
from dataclasses import dataclass

@dataclass
class DomainEvent:
    """Base Domain Event"""
    pass

class DomainEventDispatcher:
    _handlers: dict[Type[DomainEvent], List[Callable]] = {}

    @classmethod
    def subscribe(cls, event_type: Type[DomainEvent], handler: Callable):
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def dispatch(cls, event: DomainEvent):
        handlers = cls._handlers.get(type(event), [])
        for handler in handlers:
            handler(event)

# Simple global dispatcher for the module
dispatcher = DomainEventDispatcher()
