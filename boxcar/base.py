from abc import ABC, abstractmethod


class BoxCarObject(ABC):
    def __init__(self, base_type: str):
        self.base_type = base_type
        
    @abstractmethod
    def destroy(self):
        raise Exception("Please implement destroy()")

    