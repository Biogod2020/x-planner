from __future__ import annotations

import json
from typing import Any

from mcp_server.tools import repository_for
from mission_core.models import MissionStatus

RESOURCE_URIS = [
    "mission://today",
    "mission://missions/active",
    "mission://mission/{id}",
    "mission://capacity/recent",
    "mission://review/due",
    "mission://risks/open",
]


def _json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def get_status_brief_resource(db_path: str | None = None, day: str | None = None) -> str:
    return _json(repository_for(db_path).get_status_brief(day=day))


def get_active_missions_resource(db_path: str | None = None) -> str:
    missions = repository_for(db_path).list_missions(MissionStatus.ACTIVE)
    return _json([mission.model_dump(mode="json") for mission in missions])


def get_mission_resource(id: int, db_path: str | None = None) -> str:
    repository = repository_for(db_path)
    mission = repository.get_mission(id).model_dump(mode="json")
    tasks = [task.model_dump(mode="json") for task in repository.list_tasks(mission_id=id)]
    return _json({"mission": mission, "tasks": tasks})


def get_capacity_recent_resource(db_path: str | None = None) -> str:
    logs = repository_for(db_path).list_recent_capacity()
    return _json([log.model_dump(mode="json") for log in logs])


def get_review_due_resource(db_path: str | None = None) -> str:
    tasks = repository_for(db_path).list_reviews_due()
    return _json([task.model_dump(mode="json") for task in tasks])


def get_open_risks_resource(db_path: str | None = None) -> str:
    risks = repository_for(db_path).list_open_risks()
    return _json([risk.model_dump(mode="json") for risk in risks])
