---
title: Support Queue Environment Server
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - environment
  - rl
  - multi-agent
---

# 🎯 Scaler: OpenEnv Support Queue Environment

> A **real-world AI training environment** for customer support triage and decision-making, featuring deterministic grading, shaped rewards, and multi-difficulty tasks.

[![GitHub](https://img.shields.io/badge/github-BGokulKrishnaSai/Scaler-blue?logo=github)](https://github.com/BGokulKrishnaSai/Scaler)
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![OpenEnv](https://img.shields.io/badge/openenv-spec%201.0-orange)](https://openenv.dev)

---

## 📋 Overview

**Scaler** is a production-ready OpenEnv environment for training AI agents to handle real-world customer support tasks. Agents must:
- 📨 Analyze inbound customer messages
- 🔍 Review account context and policy constraints
- 📝 Complete structured support records
- ✉️ Draft appropriate customer replies
- 🎯 Make correct business decisions (refunds, escalations, priorities)

### ✨ Key Features

✅ **Real-World Complexity** — Not games; genuine support scenarios  
✅ **Deterministic Grading** — Reproducible, verifiable scoring  
✅ **Shaped Rewards** — Progress incentives over full trajectories  
✅ **Multi-Difficulty** — Easy → Medium → Hard with scaled time budgets  
✅ **Procedural Variants** — Infinite seeds with fixed expected outcomes  
✅ **OpenEnv Compliant** — Standard `reset()` / `step()` / `state()` API  
✅ **FastAPI Server** — Live HTTP endpoints at http://localhost:8000/docs  

---

## 🚀 Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/BGokulKrishnaSai/Scaler.git
cd Scaler
pip install -e .
```

### Run Server Locally

```bash
python -m support_queue_env.server.app
# API docs at: http://localhost:8000/docs
```

### Try Your First Task

```python
from support_queue_env.server.support_queue_environment import SupportQueueEnvironment
from support_queue_env.models import SupportQueueAction

env = SupportQueueEnvironment()

# Reset to an easy task
obs = env.reset(task_id="easy_password_reset", seed=0)
print(f"Objective: {obs.objective}")
print(f"Customer Message: {obs.customer_message}")

# Take an action
action = SupportQueueAction(queue="account_access", priority="high", submit=True)
obs = env.step(action)
print(f"Reward: {obs.reward}")
print(f"Final Score: {obs.score_breakdown['overall']}")
```

---

## 📚 Task Descriptions

Each task tests different aspects of customer support reasoning:

| Task | Difficulty | Time Budget | Focus Area | Key Metrics |
|------|-----------|-------------|-----------|------------|
| **easy_password_reset** | ⭐ Easy | 4 steps | Quick account access resolution | Queue accuracy, priority setting |
| **medium_duplicate_charge** | ⭐⭐ Medium | 6 steps | Financial decision-making | Refund correctness, amount precision |
| **hard_admin_compromise** | ⭐⭐⭐ Hard | 8 steps | Security incident triage | Escalation routing, tag coverage |

**All tasks** are graded on a **0.0–1.0 scale** with detailed component breakdowns.

---

## 🎮 API Reference

### Core Methods

#### `reset(seed, task_id, episode_id) → Observation`

Initialize an episode with optional task selection and seeding.

```python
# Random task
obs = env.reset()

# Specific task with seed
obs = env.reset(task_id="medium_duplicate_charge", seed=42)

# With custom episode ID
obs = env.reset(task_id="easy_password_reset", episode_id="exp-001")
```

**Returns:** `SupportQueueObservation` containing:
- Task metadata (`task_id`, `difficulty`, `title`, `objective`)
- Work inputs (`customer_message`, `account_snapshot`, `policy_snippets`)
- Initial `current_record` (empty `TicketRecord`)
- Initial `score_breakdown`

---

#### `step(action) → Observation`

Execute an action and receive reward + updated observation.

```python
action = SupportQueueAction(
    queue="billing",
    priority="normal",
    escalation_team="billing_ops",
    status="escalated",
    refund_decision="partial",
    refund_amount=25.50,
    tags=["billing", "refund", "verified"],
    internal_notes="Customer has valid receipt. Approved partial refund.",
    reply_draft="We've reviewed your account and approved a $25.50 refund.",
    submit=True  # Finalize and grade
)

obs = env.step(action)
# obs.reward: float (shaped reward signal)
# obs.done: bool (episode finished)
# obs.score_breakdown: dict (detailed grading)
```

**Returns:** `SupportQueueObservation` with:
- Updated `current_record` (your changes applied)
- New `score_breakdown` (after grading)
- `reward` (scalar signal)
- `done` (whether episode finished)
- `feedback` (environment notes)

---

#### `state() → SupportQueueState`

Access full internal episode state.

```python
state = env.state
print(state.cumulative_reward)  # Sum of all rewards
print(state.final_score)        # Graded score
print(state.submitted)          # Episode finalized?
print(state.current_record)     # Current ticket state
```

---

## 💰 Reward Shaping

Agents learn through a carefully designed reward function:

```
reward = (current_score - previous_score) × 1.5    # Score improvement bonus
       - 0.02                                        # Step cost (discourage bloat)
       - 0.05 * [no_op]                            # No-op penalty (encourage action)
       - 0.05 * [unexpected_refund]                # Safety penalty
       + (final_score - 0.05) * [submit]           # Submission bonus (scaled by quality)
       - 0.05 * [auto_submit]                      # Budget exceeded penalty
```

**Design Principles:**
- ✅ Agents learn to improve incrementally
- ✅ Discourage time-wasting (step cost)
- ✅ Encourage decisive action (no-op penalty)
- ✅ Penalize unsafe decisions (unexpected refund)
- ✅ Reward clean submission (submission bonus)

---

## 📊 Grading Breakdown

Deterministic grader with component-level scoring:

| Component | Weight | Criteria | Score Range |
|-----------|--------|----------|-------------|
| **Queue** | 15% | Correct department assignment | 0.0–1.0 |
| **Priority** | 15% | Urgency level matching | 0.0–1.0 |
| **Escalation** | 15% | Route to correct team | 0.0–1.0 |
| **Status** | 10% | Ticket state accuracy | 0.0–1.0 |
| **Refund** | 25% | Decision + amount precision | 0.0–1.0 |
| **Tags** | 10% | Required tag coverage | 0.0–1.0 |
| **Reply** | 10% | Keyword requirements met | 0.0–1.0 |
| **OVERALL** | 100% | Weighted total | 0.0–1.0 |

---

## 🔄 Advanced Features

### Procedural Task Variants

Infinite training variety without task memorization:

```python
# Same task, different seeds → varied customer messages
# But expected outcomes remain fixed for reproducible grading

for seed in range(100):
    obs = env.reset(task_id="medium_duplicate_charge", seed=seed)
    # Different: customer_message, account_snapshot, urgency
    # Same: expected refund_decision, expected refund_amount
    
    # Your agent experiences 100 different scenarios
    # Each with deterministic, known correct answer
```

**Use Cases:**
- Training robust agents (avoid overfitting wording)
- Generating evaluation datasets
- Multi-environment training sweeps

---

### Difficulty-Scaled Step Budgets

Fair time allocation based on task complexity:

```
Easy   → 4 steps   (quick decisions, time pressure)
Medium → 6 steps   (balanced reasoning + action)
Hard   → 8 steps   (complex security reasoning)
```

Automatically applied via `_get_difficulty_scaled_max_steps()`.

---

### Multi-Agent Coordination

Framework for distributed specialist teams:

```python
from support_queue_env.multi_agent import MultiAgentCoordinator, RoutingAgent

coordinator = MultiAgentCoordinator({
    "router": RoutingAgent(),
    "billing": BillingSpecialist(),
    "security": SecuritySpecialist(),
})

# Agents debate and reach consensus
action = coordinator.coordinate(obs, max_rounds=2)
obs = env.step(action)
```

See `multi_agent.py` for full implementation.

---

## 📦 Project Structure

```
Scaler/
├── 📂 server/
│   ├── app.py                           # FastAPI server
│   └── support_queue_environment.py       # Env implementation
├── models.py                             # Pydantic types
├── graders.py                            # Deterministic scoring
├── tasks.py                              # Task definitions
├── baseline.py                           # OpenAI inference
├── multi_agent.py                        # Multi-agent framework
├── 📂 tests/                             # Unit tests
├── openenv.yaml                          # OpenEnv spec
├── Dockerfile                            # Container setup
├── pyproject.toml                        # Dependencies
└── uv.lock                               # Locked versions
```

---

## 🧪 Testing

```bash
# Run full test suite
pytest tests/ -v

# Run specific test
pytest tests/test_support_queue_environment.py::test_reset -v

# Check OpenEnv compliance
python validation_check.py

# Check step budgets
python test_scaled_steps.py
```

---

## 🐳 Docker & Deployment

### Local Development

```bash
docker build -t scaler-env .
docker run -p 8000:8000 scaler-env
# API available at http://localhost:8000/docs
```

### Hugging Face Spaces

Deploy to HF Spaces (pre-configured):

```bash
# 1. Create space on huggingface.co/spaces
# 2. Add as remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/Scaler

# 3. Push to deploy
git push hf main
# HF auto-builds Docker image and hosts live
```

---

## 📖 Usage Examples

### Example 1: Single Episode with Claude

```python
import anthropic
from support_queue_env.server.support_queue_environment import SupportQueueEnvironment
from support_queue_env.models import SupportQueueAction

env = SupportQueueEnvironment()
client = anthropic.Anthropic()

obs = env.reset(task_id="medium_duplicate_charge")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=500,
    messages=[{"role": "user", "content": f"Task: {obs.objective}\n\n{obs.customer_message}"}]
)

# Parse response...
action = SupportQueueAction(queue="billing", submit=True)
obs = env.step(action)
print(f"Score: {obs.score_breakdown['overall']:.2f}")
```

### Example 2: Benchmark Over Seeds

```python
results = {}
for seed in range(10):
    obs = env.reset(task_id="hard_admin_compromise", seed=seed)
    # Agent acts...
    obs = env.step(action)
    results[seed] = {
        "reward": obs.cumulative_reward,
        "score": obs.score_breakdown["overall"]
    }

avg_score = sum(r["score"] for r in results.values()) / len(results)
print(f"Avg Score: {avg_score:.3f}")
```

---

## 📄 Documentation Files

- **[REQUIREMENTS_CHECKLIST.md](REQUIREMENTS_CHECKLIST.md)** — Functional & non-functional requirements verification
- **[VALIDATION_REPORT.md](VALIDATION_REPORT.md)** — OpenEnv spec compliance validation results
- **[EVALUATION_REPORT.md](EVALUATION_REPORT.md)** — Agent evaluation metrics & benchmarks
- **[PERFECT_SCORE_REPORT.md](PERFECT_SCORE_REPORT.md)** — Perfect-play trajectories

---

## 🔗 Reference

- **OpenEnv Spec:** https://github.com/openenv/openenv
- **OpenAI Python:** https://github.com/openai/openai-python
- **FastAPI:** https://fastapi.tiangolo.com/

---

## 📞 Support

**Issues & Questions:**
- 🐛 [GitHub Issues](https://github.com/BGokulKrishnaSai/Scaler/issues)
- 📚 [API Docs](http://localhost:8000/docs) (after running server)

**Live Server:**
```bash
python -m support_queue_env.server.app
# Then visit: http://localhost:8000/docs
```

---

**Start training your agent now:**

```bash
git clone https://github.com/BGokulKrishnaSai/Scaler.git
cd Scaler
pip install -e .
python -m support_queue_env.server.app
```

🚀 **Your AI agent awaits!**
