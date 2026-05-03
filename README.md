# Crypto Agent Research

Five-agent crypto-research loop powered by the Anthropic SDK. **The point of the
project is not to make money** — it's to study how an LLM agent team **thinks,
uses tools, and reflects** when run inside a continuous decision loop with
real-world market data.

> ⚠️ **Compliance & risk.** This system makes no real trades. It reads Binance
> public data only. Crypto is high-risk and may go to zero. Any future version
> that connects real funds requires KDAN legal / compliance review under PDPA,
> GDPR, and CCPA. *Please verify with KDAN's legal or compliance team before
> finalizing.*

## The team

| Agent       | Model               | Job                                                               |
| ----------- | ------------------- | ----------------------------------------------------------------- |
| Scout       | `claude-haiku-4-5`  | Pick 3-5 USDT pairs worth a closer look                           |
| Analyst     | `claude-sonnet-4-6` | One technical memo per candidate (no trade calls)                 |
| Trader      | `claude-opus-4-7`   | Read memos + lessons; pick BUY/HOLD with reasoning                |
| Risk        | `claude-haiku-4-5`  | Cheap rule check (size cap, spot only, valid action)              |
| Reflector   | `claude-opus-4-7`   | Every Nth cycle: read history, write one lesson for future cycles |

The model split is deliberate — Scout/Risk are routine, Analyst is structured
analysis, Trader/Reflector get the most capable model. Models are configurable
via `.env` so you can A/B them.

## Architecture

```
app/
├── core/          indicators / memory / prompts (pure)
├── services/      market_data / tools / agent / team / orchestrator
├── api/           FastAPI routers (cycles, memory)
└── web/           Streamlit UI (trace + lessons + decisions)
```

Memory is plain JSONL under `./data/` (gitignored): `decisions.jsonl`,
`outcomes.jsonl`, `lessons.jsonl`. Wipe with `rm -rf data/` to start fresh.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Run

Terminal A — API:

```bash
API_PORT=8204 ./scripts/dev_api.sh
```

Terminal B — UI:

```bash
UI_API_URL=http://127.0.0.1:8204 streamlit run app/web/streamlit_app.py --server.port 8604
```

Open http://127.0.0.1:8604, click **Run cycle**, watch the trace panel. Each
agent's prompt response, tool calls, and token usage are visible per turn.

## API

```bash
curl -s http://127.0.0.1:8204/api/health
curl -s -X POST http://127.0.0.1:8204/api/cycles/run -H 'content-type: application/json' -d '{"reflect": true}'
curl -s 'http://127.0.0.1:8204/api/decisions?limit=5'
curl -s 'http://127.0.0.1:8204/api/lessons'
```

## Tests

```bash
PYTHONPATH=. pytest                       # unit tests, no Anthropic calls
PYTHONPATH=. python scripts/smoke_cycle.py  # one real cycle (spends tokens)
./scripts/fmt_lint.sh                       # ruff format + check
```

## Research notes (fill in as you run cycles)

- Lessons evolution after N cycles: *(record the first 5 vs. the last 5)*
- Cumulative token usage / cache hit rate per agent: *(record from the trace)*
- Observed quirks: *(does Trader fixate on a symbol? are Reflector lessons
  generic? does the Scout pick mostly blue chips?)*

These observations are the deliverable, not P&L.

## Out of scope (not in this MVP)

- Real-money trading or live order execution
- WebSocket streaming
- Historical backtests
- Long-term vector memory
- Web3 / on-chain data
