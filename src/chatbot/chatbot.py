from typing import Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


def run_chatbot(user_input: str, llm: LLMProvider, system_prompt: Optional[str] = None) -> str:
    """Baseline chatbot: direct single-shot response without tool usage."""
    result = llm.generate(user_input, system_prompt=system_prompt)
    tracker.track_request(
        provider=result.get("provider", "unknown"),
        model=llm.model_name,
        usage=result.get("usage", {}),
        latency_ms=result.get("latency_ms", 0),
    )
    logger.log_event("CHATBOT_RESPONSE", {"input": user_input, "output": result.get("content", "")})
    return result.get("content", "")
