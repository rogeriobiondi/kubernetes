from .base import ModeratorBase
 
class EntryPoint(ModeratorBase):
    """
        Entrypoint class for moderator "first"
    """
 
    def moderate(self, tracking: dict, event: dict, args: dict) -> dict:
        """
            Check if the event is the first event in the package tracking
        """
        print("first: running moderator.")
        events = tracking['events']
        # If there is no event, return false
        if len(events) < 1:
            return False
        # Check if the first event on the list is the current event
        return events[0]["_id"] == event["_id"]