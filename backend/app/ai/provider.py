from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_summary(self, text: str, prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured executive summary from tender content."""
        pass

    @abstractmethod
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate vector embedding array for semantic search."""
        pass
