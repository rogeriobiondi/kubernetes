from .base import ModeratorBase
 
class EntryPoint(ModeratorBase):
    """
        Entrypoint class for moderator "depends_on"
    """
 
    def moderate(self, tracking: dict, event: dict, args: dict) -> dict:
        """
            Check if the event is the first event in the package tracking
        """
        print("depends_on: running moderator.")
        print(f"  checking dependency on events {args}")
        events = tracking['events']        
        # Check if the events in args already exist in timeline
        results = []
        for arg in args:
            print(f"  checking dependency on {arg}...")
            for previous_evt in events:
                print(f"  checking dependency on {arg}=={previous_evt['type']} ({previous_evt['_id']})...")
                if arg == previous_evt['type']:
                    print(f"  event found.")
                    # if found the event, register the positive result and go to the next arg
                    results.append(True)
                    break
        # If all the events has been found
        return len(results) == len(args)