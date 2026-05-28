---
description: Manage human goals with Mission Control Core using Mission Briefs, MCP state, evidence audits, one daily mainline task, and review decisions. Use when planning, tracking, completing, accepting, or reviewing tasks through mission-control.
---

# Mission Control Skill

Use this skill when managing a human goal with Mission Control Core. The database is the source of truth. Skills guide behavior; MCP tools mutate state.

## Non-Negotiables

- Never start execution on a vague task.
- Ask up to 5 clarifying questions before planning. Stop when the next action and success evidence are clear.
- Generate and persist a Mission Brief with `save_mission_brief` before creating execution tasks.
- Every task must have `next_action`, `expected_output`, and `evidence_required`.
- Recommend exactly one daily mainline task with `select_today_mainline`.
- No accepted evidence audit, no done: use `submit_evidence` and `record_evidence_audit` before asking for completion or acceptance.
- Audit submitted evidence with `record_evidence_audit` before relying on it; pending or rejected evidence is not enough for done.
- Repeated failures must escalate to one decision: shrink, split, block, pause, or kill. Record it with `run_review`.

## Routing Policy

Classify the user request before choosing a tool path:

- Vague goal: ask targeted clarification questions before planning or creating ready tasks. Ask no more than 5 questions, and stop when mission objective, constraints, next action, expected output, and evidence standard are clear.
- Evidence-free done request: refuse completion or acceptance. Ask for inspectable evidence and do not call `update_task_status` with `completed` or `accepted` until an evidence audit is accepted.
- Repeated failure: stop normal execution. Run a failure review and choose exactly one decision: shrink, split, block, pause, or kill.
- Multiple goals: choose exactly one daily mainline task. Record alternatives as non-mainline candidates only after the mainline is explicit.

## Workflow

1. Classify the request using the routing policy.
2. Clarify vague goals. Ask no more than 5 targeted questions.
3. Create the mission with `create_mission`.
4. Write the Mission Brief: goal, constraints, risks, success evidence, likely tasks, and non-goals. Persist it with `save_mission_brief`.
5. Create only ready tasks. If any of `next_action`, `expected_output`, or `evidence_required` is missing, ask another question instead of creating the task.
6. Choose one task as today's mainline with `select_today_mainline`. Do not select multiple mainline tasks for the same day.
7. During execution, submit concrete evidence with `submit_evidence`. Evidence can be command output, file paths, test output, review notes, or other inspectable artifacts.
8. Audit evidence with `record_evidence_audit`. Reject weak or irrelevant evidence.
9. Complete or accept a task only after at least one evidence audit is `accepted`. Use `update_task_status` only when the status transition is justified by accepted evidence.
10. If a task fails repeatedly, stop normal execution. Use `run_review` and choose exactly one action: shrink, split, block, pause, or kill.
11. Use `get_status_brief` at the start and end of a work session.

## Mission Brief Template

- Goal:
- Mission objective:
- Constraints and non-goals:
- Success evidence:
- Risks:
- First task candidates:
- Today's recommended mainline task:

## Evidence Standard

Evidence must be specific enough for another agent or human to inspect. Do not mark work complete based on intent, confidence, summaries without artifacts, unverifiable claims, pending audits, or rejected audits.
