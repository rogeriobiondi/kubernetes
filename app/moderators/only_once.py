from .base import ModeratorBase
 
class EntryPoint(ModeratorBase):
    """
        Entrypoint class for moderator "only_once"
    """
 
    def moderate(self, tracking: dict, event: dict, args: dict) -> dict:
        """
            Check if the same event type appears only once in the tracking
        """
        print("only_once: running moderator.")
        print(f"  checking event type {event['type']}.")
        events = tracking['events']
        count = 0
        for e in events:                        
            if e['type'] == event['type']:
                count+=1
            print(f"  checking event {event['type']} == {e['type']} ({count}).")
        return (count == 1)