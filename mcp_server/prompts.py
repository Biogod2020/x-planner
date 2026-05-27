MISSION_BRIEF_PROMPT = """
Create a Mission Brief before planning execution. Include: goal, mission objective, constraints, risks, success evidence, and the first task candidates. Do not create ready tasks until next_action, expected_output, and evidence_required are known.
""".strip()

FAILURE_REVIEW_PROMPT = """
A task has failed repeatedly. Review evidence and decide one action: shrink, split, block, pause, or kill. Record the decision with run_review before continuing.
""".strip()
