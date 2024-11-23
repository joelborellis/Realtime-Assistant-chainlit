from abc import ABC, abstractmethod
from pydantic import BaseModel


class BaseTool(ABC):
    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.definition = {
            "type": "function",
            "name": name,
            "description": description,
            "parameters": parameters,
        }

    @abstractmethod
    async def handle(self, **kwargs) -> dict:
        """Handle the tool's main logic."""
        pass

    def get_tool(self):
        """Return the tool's definition and handler."""
        return self.definition, self.handle
