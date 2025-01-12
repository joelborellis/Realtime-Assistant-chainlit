from .base_tool import BaseTool
from utils.utils import timeit_decorator
from dotenv import dotenv_values
from utils.memory_management import memory_manager
from typing import Any

config = dotenv_values(".env")


class AddToMemoryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="add_to_memory",
            description="Adds content to memory.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key to use for storing the value in memory.",
                    },
                    "value": {
                        "type": "string",
                        "description": "The value to store in memory.",
                    },
                },
                "required": ["key", "value"],
            },
        )

    @timeit_decorator
    async def handle(self, key: str, value: Any) -> dict:
        """
        Add a key-value pair to memory using the MemoryManager's upsert method.
        """
        success = memory_manager.upsert(key, value)
        if success:
            return {
                "status": "success",
                "message": f"Added '{key}' to memory with value '{value}'",
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to add '{key}' to memory",
            }


class IngestMemoryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ingest_memory",
            description="Returns the ACTIVE_MEMORY .env var json content",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

    @timeit_decorator
    async def handle(self) -> dict:
        """
        Returns the current memory content using memory_manager.
        """
        memory_manager.load_memory()
        memory_content = memory_manager.get_xml_for_prompt(["*"])
        return {
            "ingested_content": memory_content,
            "message": "Successfully ingested content",
            "success": True,
        }


class ResetActiveMemoryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="reset_active_memory",
            description="Resets the active memory to an empty dictionary.",
            parameters={
                "type": "object",
                "properties": {
                    "force_delete": {
                        "type": "boolean",
                        "description": "Whether to force reset the memory without confirmation. Defaults to false if not specified.",
                    },
                },
                "required": [],
            },
        )

    @timeit_decorator
    async def handle(self, force_delete: bool = False) -> dict:
        """
        Reset the active memory to an empty dictionary.
        If force_delete is False, ask for confirmation before resetting.
        """
        if not force_delete:
            return {
                "status": "confirmation_required",
                "message": "Are you sure you want to reset the active memory? This action cannot be undone. Reply with 'force delete' to confirm.",
            }

        memory_manager.reset()
        return {
            "status": "success",
            "message": "Active memory has been reset to an empty dictionary.",
        }
