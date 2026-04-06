import os
import sys
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent_v1 import ReActAgentV1
from src.repositories.json_repo import JsonShopRepository
from src.tools.registry import create_tool_registry


class MockLLMVi:
    def __init__(self):
        self.model_name = "mock-vi"
        self._step = 0

    def generate(self, prompt: str, system_prompt: str | None = None) -> Dict[str, Any]:
        self._step += 1
        if self._step == 1:
            content = (
                "Thought: Người dùng mô tả sản phẩm, mình cần lấy toàn bộ catalog trước.\n"
                "Action: list_all_products()"
            )
        else:
            content = (
                "Thought: Mình đã có danh sách và chọn được sản phẩm phù hợp.\n"
                "Final Answer: Sản phẩm phù hợp là iphone 15 (id: p001)."
            )

        return {
            "content": content,
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            "latency_ms": 5,
            "provider": "mock",
        }


def test_agent_v1_vietnamese_end_to_end_description_to_id():
    repo = JsonShopRepository(data_dir="data")
    tools = create_tool_registry(repo=repo)
    agent = ReActAgentV1(llm=MockLLMVi(), tools=tools, max_steps=4)

    question = "Tôi muốn mua mẫu điện thoại iPhone đời mới, tư vấn giúp tôi"
    answer = agent.run(question)

    assert "iphone 15" in answer.lower()
    assert "p001" in answer


def test_agent_v1_parse_action_with_vietnamese_and_code_fence():
    agent = ReActAgentV1(llm=MockLLMVi(), tools=[])

    text = '''```json
Thought: Tôi cần kiểm tra tồn kho theo mã sản phẩm.
Action: check_stock_by_id(product_id="p001")
```'''
    tool_name, args, err = agent._parse_action(text)

    assert err is None
    assert tool_name == "check_stock_by_id"
    assert args == {"product_id": "p001"}
