# Schema

Mission Control Core uses SQLite. The database is initialized by `mission_core.db.initialize_database`.

## missions

- `id` integer primary key
- `title` text, required
- `objective` text
- `status` text: active, blocked, paused, completed, killed
- `brief` text
- `created_at` text timestamp
- `updated_at` text timestamp

## tasks

- `id` integer primary key
- `mission_id` foreign key to missions
- `title` text, required
- `status` text: draft, ready, in_progress, blocked, failed, completed, accepted
- `next_action` text, required for ready tasks
- `expected_output` text, required for ready tasks
- `evidence_required` text, required for ready tasks
- `failure_count` integer
- `requires_failure_review` integer boolean
- `today_mainline_on` date text, nullable
- `created_at` text timestamp
- `updated_at` text timestamp

## evidence

- `id` integer primary key
- `task_id` foreign key to tasks
- `description` text, required
- `uri` text
- `audit_status` text: pending, accepted, rejected
- `audit_notes` text
- `created_at` text timestamp
- `audited_at` text timestamp

## reviews

- `id` integer primary key
- `mission_id` optional foreign key to missions
- `task_id` optional foreign key to tasks
- `review_type` text
- `decision` text
- `notes` text
- `created_at` text timestamp

A review must refer to either a mission or a task. Completed and killed missions require a review record.

## risks

- `id` integer primary key
- `mission_id` optional foreign key to missions
- `task_id` optional foreign key to tasks
- `description` text
- `status` text: open, mitigated, closed
- `mitigation` text
- `created_at` text timestamp
- `updated_at` text timestamp

## capacity_logs

- `id` integer primary key
- `day` date text, unique
- `available_minutes` integer
- `energy_level` integer from 1 to 5
- `notes` text
- `created_at` text timestamp

## commitments

- `id` integer primary key
- `mission_id` optional foreign key to missions
- `task_id` optional foreign key to tasks
- `description` text
- `committed_on` date text
- `due_on` date text
- `status` text: active, met, missed, canceled
- `created_at` text timestamp
- `updated_at` text timestamp
