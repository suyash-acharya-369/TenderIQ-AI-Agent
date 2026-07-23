from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_summary(self, text: str, prompt_template: str) -> Dict[str, Any]:
        """Generate structured JSON summary of tender document."""
        pass

    @abstractmethod
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate vector embedding array for semantic search."""
        pass
