import ast
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgentV1:
    """ReAct agent v1 with robust action parsing and tool execution."""

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.tool_map = {t["name"]: t for t in self.tools if "name" in t}

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t.get('description', 'No description')}" for t in self.tools]
        )
        return (
            "You are a ReAct shopping assistant.\n"
            "You must reason in steps and use tools when required.\n"
            "Available tools:\n"
            f"{tool_descriptions}\n\n"
            "Output format (strict):\n"
            "Thought: <reasoning>\n"
            "Action: <tool_name>(<arguments>)\n"
            "Observation: <filled by system>\n"
            "...\n"
            "Final Answer: <answer to user>\n\n"
            "Rules:\n"
            "1) If you need product grounding, call list_all_products first.\n"
            "2) Prefer product id for follow-up tool calls.\n"
            "3) Do not invent tools that are not listed above."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"version": "v1", "input": user_input, "model": self.llm.model_name})

        scratchpad = ""
        for step in range(1, self.max_steps + 1):
            llm_input = self._build_input(user_input, scratchpad)
            result = self.llm.generate(llm_input, system_prompt=self.get_system_prompt())
            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )

            content = (result.get("content") or "").strip()
            logger.log_event("AGENT_STEP", {"version": "v1", "step": step, "llm_output": content})

            final_answer = self._extract_final_answer(content)
            if final_answer:
                logger.log_event("AGENT_END", {"version": "v1", "steps": step, "status": "final_answer"})
                return final_answer

            tool_name, args_payload, parse_error = self._parse_action(content)
            if parse_error:
                observation = f"PARSER_ERROR: {parse_error}. Use exact format Action: tool_name(args)."
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {"version": "v1", "step": step, "error": parse_error, "output": content},
                )
                scratchpad += f"\nLLM Output:\n{content}\nObservation: {observation}\n"
                continue

            observation = self._execute_tool(tool_name, args_payload)
            logger.log_event(
                "AGENT_TOOL_CALL",
                {
                    "version": "v1",
                    "step": step,
                    "tool": tool_name,
                    "args": args_payload,
                    "observation": observation,
                },
            )
            scratchpad += f"\nLLM Output:\n{content}\nObservation: {observation}\n"

        timeout_answer = "I could not complete this request within max_steps. Please clarify your request."
        logger.log_event("AGENT_END", {"version": "v1", "steps": self.max_steps, "status": "max_steps"})
        return timeout_answer

    def _build_input(self, user_input: str, scratchpad: str) -> str:
        if not scratchpad:
            return f"User Question: {user_input}"
        return f"User Question: {user_input}\n\nContext from previous steps:\n{scratchpad}"

    def _extract_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final\s*Answer\s*:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _strip_code_fences(self, text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json|python)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def _parse_action(self, text: str) -> Tuple[Optional[str], Any, Optional[str]]:
        cleaned = self._strip_code_fences(text)

        # Try JSON action format first.
        json_match = re.search(r"Action\s*:\s*(\{.*\})", cleaned, flags=re.IGNORECASE | re.DOTALL)
        if json_match:
            try:
                payload = json.loads(json_match.group(1).strip())
                tool_name = payload.get("tool") or payload.get("name")
                args_payload = payload.get("args", {})
                if not tool_name:
                    return None, None, "JSON action missing tool field"
                return str(tool_name), args_payload, None
            except json.JSONDecodeError:
                pass

        # Try function-style actions and take the latest Action line.
        actions = re.findall(r"Action\s*:\s*(.+)", cleaned, flags=re.IGNORECASE)
        if actions:
            action_text = actions[-1].strip()
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*$", action_text, flags=re.DOTALL)
            if not m:
                return None, None, f"Invalid action format: {action_text}"
            tool_name = m.group(1)
            args_text = m.group(2).strip()
            args_payload = self._parse_args(args_text)
            return tool_name, args_payload, None

        return None, None, "No Action line found"

    def _parse_args(self, args_text: str) -> Any:
        if not args_text:
            return {}

        # JSON object/list arguments.
        if args_text.startswith("{") or args_text.startswith("["):
            try:
                return json.loads(args_text)
            except json.JSONDecodeError:
                pass

        # key=value pairs.
        kv_pairs = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*('[^']*'|\"[^\"]*\"|[^,]+)", args_text)
        if kv_pairs:
            parsed: Dict[str, Any] = {}
            for key, raw_val in kv_pairs:
                val = raw_val.strip()
                if (val.startswith("\"") and val.endswith("\"")) or (val.startswith("'") and val.endswith("'")):
                    parsed[key] = val[1:-1]
                    continue
                try:
                    parsed[key] = ast.literal_eval(val)
                except (ValueError, SyntaxError):
                    parsed[key] = val
            return parsed

        # Single value argument.
        single = args_text.strip()
        if (single.startswith("\"") and single.endswith("\"")) or (single.startswith("'") and single.endswith("'")):
            return {"value": single[1:-1]}

        try:
            return {"value": ast.literal_eval(single)}
        except (ValueError, SyntaxError):
            return {"value": single}

    def _execute_tool(self, tool_name: Optional[str], args_payload: Any) -> str:
        if not tool_name:
            return json.dumps({"error": "missing_tool_name"}, ensure_ascii=False)

        tool = self.tool_map.get(tool_name)
        if not tool:
            return json.dumps({"error": "hallucinated_tool", "tool": tool_name}, ensure_ascii=False)

        fn = tool.get("fn") or tool.get("func") or tool.get("callable")
        if not callable(fn):
            return json.dumps({"error": "tool_not_callable", "tool": tool_name}, ensure_ascii=False)

        try:
            if isinstance(args_payload, dict):
                if "value" in args_payload and len(args_payload) == 1:
                    result = fn(args_payload["value"])
                else:
                    result = fn(**args_payload)
            elif isinstance(args_payload, list):
                result = fn(*args_payload)
            else:
                result = fn(args_payload)
        except TypeError:
            # Fallback: pass raw payload as a single positional argument.
            result = fn(args_payload)
        except Exception as exc:
            return json.dumps(
                {"error": "tool_execution_error", "tool": tool_name, "message": str(exc)},
                ensure_ascii=False,
            )

        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        return str(result)
