"""
JARVIS Event Bus System

Minimal event bus for decoupling core from GUI and other subscribers.
"""
import threading
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Event types
EVENT_USER_MESSAGE = "user_message"
EVENT_TASK_STARTED = "task_started"
EVENT_PLAN_CREATED = "plan_created"
EVENT_ACTION_STARTED = "action_started"
EVENT_ACTION_COMPLETED = "action_completed"
EVENT_ACTION_FAILED = "action_failed"
EVENT_VISION_CAPTURED = "vision_captured"
EVENT_PERMISSION_REQUIRED = "permission_required"
EVENT_TASK_CANCELLED = "task_cancelled"
EVENT_TASK_COMPLETED = "task_completed"
EVENT_ERROR = "error"
EVENT_STATE_CHANGED = "state_changed"


@dataclass
class Event:
    """Event object."""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    """Simple event bus for publish/subscribe pattern."""
    
    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._global_subscribers: List[Callable[[Event], None]] = []
        self._lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> "EventBus":
        """Get singleton event bus instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Subscribe to a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable[[Event], None]):
        """Subscribe to all events."""
        with self._lock:
            self._global_subscribers.append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Unsubscribe from a specific event type."""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass
    
    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """Publish an event to all subscribers."""
        event = Event(type=event_type, data=data or {})
        
        with self._lock:
            callbacks = list(self._global_subscribers)
            if event_type in self._subscribers:
                callbacks.extend(self._subscribers[event_type])
        
        # Call subscribers outside lock to avoid deadlocks
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[EventBus] Error in subscriber: {e}")
    
    def clear(self):
        """Clear all subscriptions."""
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()


# Convenience functions using global instance
def subscribe(event_type: str, callback: Callable[[Event], None]):
    """Subscribe to an event."""
    EventBus.get_instance().subscribe(event_type, callback)


def subscribe_all(callback: Callable[[Event], None]):
    """Subscribe to all events."""
    EventBus.get_instance().subscribe_all(callback)


def publish(event_type: str, data: Optional[Dict[str, Any]] = None):
    """Publish an event."""
    EventBus.get_instance().publish(event_type, data)
