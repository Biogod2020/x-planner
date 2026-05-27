# Real-Agent Trial Protocol

Use this protocol to dogfood Mission Control Core v0.1 with real coding agents. The trial should validate behavior, not add product features. Each task starts vague on purpose. The expected behavior is the same chain:

clarify -> mission brief -> MCP save -> evidence-backed task -> audit -> review

## Trial Setup

1. Start the MCP server:

```bash
uv run python -m mcp_server.server
```

2. Connect the candidate agent to the Mission Control MCP server.
3. Give the agent one vague task at a time.
4. Record whether the agent uses MCP tools to persist mission, task, evidence, audit, and review state.
5. Do not accept completion without inspectable evidence.

## Task 1: Vague Coding Task

Prompt:

```text
Make this repo easier to maintain.
```

Expected agent behavior:

- Clarify scope before planning, asking no more than 5 questions.
- Produce a Mission Brief that defines the maintenance goal, constraints, non-goals, and success evidence.
- Save the mission and brief through MCP tools.
- Create a ready task only after `next_action`, `expected_output`, and `evidence_required` are concrete.
- Select exactly one daily mainline task.
- Submit evidence such as test output, focused diffs, or file references before completion.
- Audit the submitted evidence before relying on it.
- Run a review that records the decision and next state.

## Task 2: Vague Documentation Task

Prompt:

```text
Improve the docs so another agent understands the project.
```

Expected agent behavior:

- Clarify the target reader, missing context, and required proof before editing.
- Generate a Mission Brief covering documentation scope, non-goals, and evidence required.
- Save the mission and brief through MCP tools.
- Create one evidence-backed documentation task with a clear next action and expected output.
- Select exactly one daily mainline task.
- Submit evidence such as changed document paths and rendered or reviewed content.
- Audit whether the evidence proves the documentation improvement.
- Run a review with a decision: accept, shrink, split, block, pause, or kill.

## Task 3: Vague Project Review Task

Prompt:

```text
Review this project and tell me if it is ready.
```

Expected agent behavior:

- Clarify what readiness means and what evidence would prove it.
- Write and save a Mission Brief before creating review tasks.
- Persist the review mission through MCP tools.
- Create a ready task with explicit evidence requirements, such as test output, file inspection notes, and identified risks.
- Select exactly one daily mainline task.
- Submit concrete review evidence instead of relying on summary judgment.
- Audit the evidence for relevance and completeness.
- Run a review that records the decision and any required follow-up: accept, shrink, split, block, pause, or kill.

## Pass Criteria

A real-agent trial passes only if the agent:

- Refuses to execute vague work before clarification.
- Saves mission and brief state through MCP tools.
- Creates no ready task without `evidence_required`.
- Keeps exactly one daily mainline task.
- Submits and audits evidence before completion.
- Records a review decision before declaring the mission or task accepted.

## Fail Criteria

A trial fails if the agent:

- Treats the system like a todo list without evidence or review.
- Marks work complete without evidence.
- Creates vague ready tasks.
- Selects multiple daily mainline tasks.
- Bypasses MCP state persistence.
- Continues after repeated failure without shrink, split, block, pause, or kill review.
