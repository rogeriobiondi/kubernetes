from abc import ABC, abstractmethod
 
class ModeratorBase(ABC):
    """
        Abstract class for new moderators
    """
 
    @abstractmethod
    def moderate(self, tracking: dict, event: dict, args: dict) -> dict:
        """
            Abstract method. Every moderator must implement it.
            It will receive the tracking and event data and must return a boolean

            tracking: the most up-to-date tracking information
            event: the current event in moderation
            args: arguments passed to the validator
        """
        print("base: running moderator.")
        return True
