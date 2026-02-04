# Ensuring each daily project has *distinct* core logic

## Anti-boilerplate guardrails

1) **One domain module is mandatory**: implement at least one `app/core/<domain>.py` file with:
   - pure functions/classes
   - domain invariants
   - no FastAPI / Streamlit imports

2) **Expose the domain via API**: add at least one router `app/api/v1/routes/<domain>.py`.

3) **Test the domain**: add `tests/test_<domain>.py` that covers invariants and edge cases.

4) **Add a README problem statement** (3–10 lines): what is the “engine” of today’s app?

5) **A metric / behavior differs**: each day define one measurable property (e.g., policy match outcome, tool schema validation, WIP limit enforcement) and test it.

---

## Example project type A: Agent Tool Registry

### Distinct core logic
A registry that validates, versions, and scores tools. The differentiator is the **tool contract**:
- tool name uniqueness
- semver version constraints
- JSONSchema-like args validation
- capability tags and a ranking function

### Suggested modules
- `app/core/tool_registry.py` (domain)
- `app/services/tool_store.py` (in-memory or sqlite)
- `app/api/v1/routes/tools.py`
- `app/schemas/tools.py`

### Domain sketch
```py
# app/core/tool_registry.py
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Tool:
    name: str
    version: str
    description: str
    tags: tuple[str, ...]
    args_schema: dict[str, Any]

class RegistryError(Exception): ...

def validate_tool(tool: Tool) -> None:
    if not tool.name or "/" in tool.name:
        raise RegistryError("invalid name")
    # add: semver parse, schema shape checks

def score(tool: Tool, preferred_tags: set[str]) -> float:
    # distinct behavior: rank by tag overlap + recency/version
    overlap = len(preferred_tags.intersection(tool.tags))
    return overlap
```

### API sketch
- `POST /api/tools` register tool
- `GET /api/tools?tag=search` list

### Test idea
- registering duplicate name+version raises
- scoring prefers tag overlap

---

## Example project type B: Link Firewall

### Distinct core logic
A deterministic policy engine that decides whether a URL is allowed, blocked, or requires review.
Differentiators:
- URL normalization (punycode, scheme defaults)
- rule language (prefix match, regex, CIDR for IPs)
- scoring + explainability (which rule matched)

### Suggested modules
- `app/core/url_policy.py`
- `app/services/url_checker.py` (DNS/HTTP HEAD optional)
- `app/api/v1/routes/firewall.py`
- `app/schemas/firewall.py`

### Domain sketch
```py
# app/core/url_policy.py
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

class Decision(str, Enum):
    allow = "allow"
    block = "block"
    review = "review"

@dataclass(frozen=True)
class Rule:
    decision: Decision
    host_suffix: str | None = None
    path_prefix: str | None = None

@dataclass(frozen=True)
class Result:
    decision: Decision
    matched_rule: Rule | None
    normalized_url: str

def normalize(url: str) -> str:
    p = urlparse(url if "://" in url else "https://" + url)
    host = (p.hostname or "").lower()
    return p._replace(netloc=host).geturl()

def evaluate(url: str, rules: list[Rule]) -> Result:
    n = normalize(url)
    p = urlparse(n)
    for r in rules:
        if r.host_suffix and not (p.hostname or "").endswith(r.host_suffix):
            continue
        if r.path_prefix and not p.path.startswith(r.path_prefix):
            continue
        return Result(r.decision, r, n)
    return Result(Decision.review, None, n)
```

### API sketch
- `POST /api/firewall/evaluate` returns decision + explanation

### Test idea
- normalization makes `Example.COM` match `.com` suffix rule
- first-match semantics

---

## Example project type C: Taskboard (Kanban-lite)

### Distinct core logic
A workflow engine that enforces invariants:
- state machine: todo → doing → done
- WIP limits per column
- ordering rules / priorities
- audit trail (events)

### Suggested modules
- `app/core/taskboard.py`
- `app/services/task_repo.py` (in-memory/db)
- `app/api/v1/routes/board.py`
- `app/schemas/board.py`

### Domain sketch
```py
# app/core/taskboard.py
from dataclasses import dataclass
from enum import Enum

class Column(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"

@dataclass
class Task:
    id: str
    title: str
    column: Column = Column.todo

class BoardError(Exception): ...

def move(task: Task, to: Column, doing_wip: int, doing_limit: int) -> Task:
    if task.column == Column.done and to != Column.done:
        raise BoardError("done is terminal")
    if to == Column.doing and doing_wip >= doing_limit:
        raise BoardError("WIP limit reached")
    task.column = to
    return task
```

### API sketch
- `POST /api/board/tasks` create
- `POST /api/board/tasks/{id}/move` enforce WIP

### Test idea
- cannot move out of done
- WIP limit blocks move into doing
