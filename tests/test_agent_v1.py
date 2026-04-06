import pytest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent_v1 import ReActAgentV1

class MockLLM:
    def __init__(self):
        self.model_name = "mock"

def test_parse_action_json():
    agent = ReActAgentV1(llm=MockLLM(), tools=[])
    
    text = '''Thought: I need to search.
Action: {"tool": "search", "args": {"query": "laptop"}}
Observation: '''
    tool_name, args, err = agent._parse_action(text)
    
    assert err is None
    assert tool_name == "search"
    assert args == {"query": "laptop"}

def test_parse_action_function():
    agent = ReActAgentV1(llm=MockLLM(), tools=[])
    
    text = '''Thought: I need to use the calculate tool.
Action: calculate(amount=500, tax=0.1)
Observation: '''
    tool_name, args, err = agent._parse_action(text)
    
    assert err is None
    assert tool_name == "calculate"
    assert args == {"amount": 500, "tax": 0.1}

def test_parse_action_missing():
    agent = ReActAgentV1(llm=MockLLM(), tools=[])
    
    text = '''Thought: I know the answer now.
Final Answer: 550
'''
    tool_name, args, err = agent._parse_action(text)
    
    assert err is not None
    assert "No Action line found" in err

def test_parse_action_vietnamese():
    agent = ReActAgentV1(llm=MockLLM(), tools=[])
    
    text = '''Thought: Tôi cần kiểm tra thông tin sản phẩm và tính thuế nhé.
Action: calc_tax(amount=1000, region="VN")
Observation: '''
    tool_name, args, err = agent._parse_action(text)
    
    assert err is None
    assert tool_name == "calc_tax"
    assert args == {"amount": 1000, "region": "VN"}

def test_extract_final_answer():
    agent = ReActAgentV1(llm=MockLLM(), tools=[])
    
    text = '''Thought: I have the information.
Final Answer: The price is $1000.
'''
    ans = agent._extract_final_answer(text)
    assert ans == "The price is $1000."
