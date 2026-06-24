"""
Event-Driven Architecture (Observer Pattern)
=============================================
Decouples core business logic from side effects.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Type
import logging

logger = logging.getLogger(__name__)

class Event:
    """Base class for all events."""
    def __init__(self, **kwargs):
        self.payload = kwargs
        self.name = self.__class__.__name__

class FeePaidEvent(Event):
    """Triggered when a fee is successfully paid."""
    pass

class EventListener(ABC):
    """Observer interface."""
    @abstractmethod
    def handle(self, event: Event):
        pass

class EmailListener(EventListener):
    """Concrete Observer: Sends confirmation emails."""
    def handle(self, event: Event):
        logger.info(f"[EmailListener] Simulated sending email for {event.name} | Payload: {event.payload}")

class AuditListener(EventListener):
    """Concrete Observer: Logs actions to the audit trail."""
    def handle(self, event: Event):
        logger.info(f"[AuditListener] Auditing {event.name} | Payload: {event.payload}")

class EventDispatcher:
    """Event Dispatcher to manage event routing (Singleton-like class methods)."""
    _listeners: Dict[Type[Event], List[EventListener]] = {}

    @classmethod
    def subscribe(cls, event_type: Type[Event], listener: EventListener):
        """Register a listener for a specific event type."""
        if event_type not in cls._listeners:
            cls._listeners[event_type] = []
        cls._listeners[event_type].append(listener)

    @classmethod
    def dispatch(cls, event: Event):
        """Notify all subscribed listeners."""
        listeners = cls._listeners.get(type(event), [])
        for listener in listeners:
            try:
                listener.handle(event)
            except Exception as e:
                logger.error(f"Error in listener {listener.__class__.__name__}: {e}")

# Setup Global Listeners
EventDispatcher.subscribe(FeePaidEvent, EmailListener())
EventDispatcher.subscribe(FeePaidEvent, AuditListener())
