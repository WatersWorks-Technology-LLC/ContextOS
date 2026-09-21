from typing import Dict, Any, List
import re

class TaskClassifier:
    """
    Task classification and intent analysis engine.
    """
    @classmethod
    def classify(cls, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        category = "general"
        if any(w in prompt_lower for w in ["fix", "bug", "error", "exception", "traceback", "crash"]):
            category = "debugging"
        elif any(w in prompt_lower for w in ["add", "implement", "build", "feature", "create"]):
            category = "feature_work"
        elif any(w in prompt_lower for w in ["refactor", "clean", "restructure", "rename"]):
            category = "refactoring"
        elif any(w in prompt_lower for w in ["why", "architecture", "design", "explain"]):
            category = "architecture_query"

        # Extract target symbols / filenames
        tokens = re.findall(r'[a-zA-Z_]\w+\.(?:py|ts|js|md|json|toml|rs|go|java|c|cpp)', prompt)

        return {
            "category": category,
            "prompt_length": len(prompt),
            "target_files": list(set(tokens)),
            "needs_rerank": len(prompt) > 200 or category == "debugging"
        }
