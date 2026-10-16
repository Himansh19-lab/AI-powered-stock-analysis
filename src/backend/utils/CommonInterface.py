from abc import ABC, abstractmethod

class ComponentInterface(ABC):
    
    @abstractmethod
    def invoke(self, *args, **kwargs):
        pass