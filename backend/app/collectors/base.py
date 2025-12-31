from abc import ABC, abstractmethod
from datetime import datetime


class BaseCollector(ABC):
    """Base class for all data collectors."""

    name: str = "base"

    def __init__(self):
        self.last_run: datetime | None = None
        self.errors: list[str] = []

    @abstractmethod
    async def collect(self) -> dict:
        """Execute the collection. Must be implemented by subclasses."""
        pass

    async def run(self) -> dict:
        """Run the collector with error handling."""
        self.errors = []
        try:
            result = await self.collect()
            self.last_run = datetime.now()
            return {
                "status": "success",
                "collector": self.name,
                "timestamp": self.last_run.isoformat(),
                "data": result,
            }
        except Exception as e:
            self.errors.append(str(e))
            return {
                "status": "error",
                "collector": self.name,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
