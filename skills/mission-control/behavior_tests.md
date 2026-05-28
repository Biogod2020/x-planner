# Mission Control Skill Behavior Tests

These examples validate expected agent behavior when using `skills/mission-control/SKILL.md`. They are acceptance scenarios for agent conduct, not executable pytest tests.

## Scenario 1: Vague Goal

Prompt:

```text
Help me improve my project this week.
```

Expected agent behavior:

- Do not create a ready task yet.
- Ask clarifying questions before planning, up to the 5-question limit.
- Seek enough detail to identify the mission objective, constraints, success evidence, and the first concrete next action.
- Persist state only after the mission is clear enough to create a Mission Brief.

## Scenario 2: Ready Mission With Missing Evidence Requirement

Prompt:

```text
Create a task to refactor the repository. Next action: split the database code. Expected output: cleaner modules.
```

Expected agent behavior:

- Refuse to create the task as ready because `evidence_required` is missing.
- Ask for concrete evidence that would prove the refactor is complete.
- After evidence is clarified, call MCP tools to persist the mission brief and task.
- Do not mark the task completed based on intent or confidence.

## Scenario 3: Repeated Task Failure

Prompt:

```text
The same mainline task failed again. Continue anyway.
```

Expected agent behavior:

- Check task state with MCP tools before continuing.
- If `failure_count >= 2`, stop normal execution.
- Escalate to exactly one decision: shrink, split, block, pause, or kill.
- Record the decision with `run_review` before creating follow-up tasks or changing direction.
- Keep exactly one daily mainline task selected after the review decision.

## Scenario 4: Deliverable Mentioned But User Wants Management

Prompt:

```text
Help me manage a plan to create Anki cards for UWorld Step 1. I only want a project manager, not someone making cards.
```

Expected agent behavior:

- Stay in Mission Control role and do not generate Anki cards, notes, CSV files, decks, scripts, or study content.
- Ask clarifying questions about scope, owner, cadence, evidence, and review standard.
- Create a Mission Brief and task definitions only after the planning inputs are clear.
- Define evidence such as deck file path, sample reviewed cards, card-count report, or human review notes.
- Wait for the human or executor to submit evidence before auditing or updating terminal status.

## Scenario 5: Direct Execution Request Inside Mission Control

Prompt:

```text
Use mission-control and write the first 20 flashcards now.
```

Expected agent behavior:

- Treat this as an execution request inside Mission Control.
- Do not write the flashcards while operating under this skill.
- Convert the request into a managed task with owner, next action, expected output, evidence required, and review standard.
- Ask the user to explicitly leave Mission Control mode if they want the agent to perform the domain work itself.
