from abc import ABC, abstractmethod
from typing import Iterable

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompts: Iterable[str]) -> Iterable[str]:
        """Yield one response per prompt in the same order."""
        raise NotImplementedError
