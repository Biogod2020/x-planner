# Mission Control Examples

## Task Creation

Good task:

- title: Add schema tests
- next_action: Write pytest coverage for mission and task transitions
- expected_output: Tests fail before implementation and pass after repository logic exists
- evidence_required: `uv run pytest tests/test_tasks.py -q` output

Bad task:

- title: Improve project
- next_action: Make it better
- expected_output: Better project
- evidence_required: empty

The bad task is vague and must not be created.

## Failure Review

If a task reaches `failure_count >= 2`, record a review decision before continuing. Valid decisions are shrink, split, block, pause, or kill.
