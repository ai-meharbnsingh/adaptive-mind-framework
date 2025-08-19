# 01_Framework_Core/telemetry/event_bus.py - Mock for Session 8
class EventBus:
    def publish(self, *args, **kwargs): pass
    def shutdown(self): pass

event_bus = EventBus()
