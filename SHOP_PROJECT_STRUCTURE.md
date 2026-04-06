# Shop Advisor Architecture for Lab 3

This architecture is designed to match the Lab 3 flow in Instructor Guide:
1) tool design first,
2) baseline chatbot,
3) ReAct agent v1,
4) iterative improvement to v2 using logs.

## 1. Recommended Structure

- src/
  - agent/
    - agent.py                      # ReAct loop (existing TODO file)
  - chatbot/
    - chatbot.py                    # Baseline chatbot without tool loop
  - core/
    - llm_provider.py
    - openai_provider.py
    - gemini_provider.py
    - local_provider.py
  - prompts/
    - system_prompts.py             # Prompt templates for chatbot, agent v1, agent v2
  - repositories/
    - json_repo.py                  # Read product/coupon/shipping data from JSON
    - sqlite_repo.py                # Read same data from SQLite
  - telemetry/
    - logger.py
    - metrics.py
  - tools/
    - catalog_tools.py              # check_stock, search_product
    - pricing_tools.py              # get_price, get_discount, calc_total
    - shipping_tools.py             # calc_shipping
- data/
  - products.sample.json
  - coupons.sample.json
- db/
  - schema.sql
- scripts/
  - init_sqlite.py                  # build SQLite from JSON sample
- tests/
  - fixtures/
  - test_local.py

## 2. Domain Scenario Mapping (Smart E-commerce Assistant)

Mandatory tools (from Instructor Guide suggestion):
- check_stock(item_name)
- get_discount(coupon_code)
- calc_shipping(weight, destination)

Recommended extra tools for richer benchmark:
- get_price(item_name)
- calc_total(item_name, quantity, coupon_code, destination)

## 3. Data Source Strategy

Use a repository abstraction so tools do not care about backend storage:
- JSON mode for quick demo and easy debugging.
- SQLite mode for realistic querying and filtering.

Runtime config idea:
- DATA_BACKEND=json | sqlite
- JSON_DATA_DIR=./data
- SQLITE_PATH=./db/shop.db

## 4. Execution Flow

A) Chatbot baseline
- Input -> LLM direct response (no tool call).
- Used to show failure on multi-step tasks.

B) Agent v1
- Input -> Thought -> Action -> Observation loop.
- Parse action robustly.
- Stop at Final Answer or max_steps.

C) Agent v2
- Improve prompt and tool descriptions using failure traces.
- Add guardrails for parser errors, hallucinated tools, and loops.

## 5. Telemetry and Evaluation

For each LLM call and tool call, log:
- provider/model
- prompt/completion tokens
- latency_ms
- step index
- selected tool and arguments
- failure type (parse_error, hallucinated_tool, timeout)

Use logs to compare:
- Chatbot vs Agent
- Agent v1 vs Agent v2

## 6. Suggested Milestones

1. Implement repository layer with JSON first.
2. Implement the 3 mandatory tools.
3. Finish chatbot baseline script.
4. Complete ReAct loop in src/agent/agent.py.
5. Add SQLite backend and switch via env.
6. Run benchmark cases and write reports.
