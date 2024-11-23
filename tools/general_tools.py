from datetime import datetime
from .base_tool import BaseTool
from utils.utils import timeit_decorator
import random

class GetCurrentTimeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="Returns the current time.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @timeit_decorator
    async def handle(self, **kwargs):
        return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

class GetRandomNumberTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_random_number",
            description="Returns a random number between 1 and 100.",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    @timeit_decorator
    async def handle(self, **kwargs):
        return {"random_number": random.randint(1, 100)}
