# Mission Control Skill

Use this skill when managing a human goal with Mission Control Core. The database is the source of truth. Skills guide behavior; MCP tools mutate state.

## Non-Negotiables

- Never start execution on a vague task.
- Ask up to 5 clarifying questions before planning. Stop when the next action and success evidence are clear.
- Generate and persist a Mission Brief with `save_mission_brief` before creating execution tasks.
- Every task must have `next_action`, `expected_output`, and `evidence_required`.
- Recommend exactly one daily mainline task with `select_today_mainline`.
- No evidence, no done: use `submit_evidence` before asking for completion or acceptance.
- Audit submitted evidence with `record_evidence_audit` before relying on it.
- Repeated failures must escalate to one decision: shrink, split, block, pause, or kill. Record it with `run_review`.

## Workflow

1. Clarify the goal. Ask no more than 5 targeted questions.
2. Create the mission with `create_mission`.
3. Write the Mission Brief: goal, constraints, risks, success evidence, likely tasks, and non-goals. Persist it with `save_mission_brief`.
4. Create only ready tasks. If any of `next_action`, `expected_output`, or `evidence_required` is missing, ask another question instead of creating the task.
5. Choose one task as today's mainline with `select_today_mainline`. Do not select multiple mainline tasks for the same day.
6. During execution, submit concrete evidence with `submit_evidence`. Evidence can be command output, file paths, test output, review notes, or other inspectable artifacts.
7. Audit evidence with `record_evidence_audit`. Reject weak or irrelevant evidence.
8. Complete or accept a task only after evidence exists. Use `update_task_status` only when the status transition is justified by evidence.
9. If a task fails repeatedly, stop normal execution. Use `run_review` and choose exactly one action: shrink, split, block, pause, or kill.
10. Use `get_status_brief` at the start and end of a work session.

## Mission Brief Template

- Goal:
- Mission objective:
- Constraints and non-goals:
- Success evidence:
- Risks:
- First task candidates:
- Today's recommended mainline task:

## Evidence Standard

Evidence must be specific enough for another agent or human to inspect. Do not mark work complete based on intent, confidence, summaries without artifacts, or unverifiable claims.
