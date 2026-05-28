# Mission Control Planner 使用教程

这份教程面向第一次使用 Mission Control Planner 的人和 AI agent。它解释如何把一个模糊目标变成可执行、可审计、可复盘的 Mission 工作流。

Mission Control Planner 不是 todo app，也不是日历、提醒、邮件或网页产品。它是一个本地优先的执行核心：

- SQLite 数据库保存真实状态。
- MCP server 提供工具给 agent 调用。
- `mission-control` skill 约束 agent 的工作方式。
- 任何任务都必须有证据，且证据 audit 被接受后，才能进入 `completed` 或 `accepted`。

核心链路：

```text
Goal -> Mission -> Task -> Evidence -> Review -> Decision
```

## 1. 你应该用它解决什么问题

适合：

- 让 agent 管理一个需要多步推进的目标。
- 避免“看起来完成了”但没有证据的任务。
- 让下一个 agent 能接手当前状态。
- 用 Mission Brief 记录目标、约束、风险、证据标准和下一步。
- 通过 review 做接受、阻塞、缩小、拆分、暂停或终止决策。

不适合：

- 日历排程。
- 通知和提醒。
- 多用户协作。
- Web UI 或移动端任务管理。
- 自动把一堆任务都排进今天。

## 2. 基本概念

### Goal

用户说出的目标，通常是自然语言，可能很模糊。

例子：

```text
帮我改进这个项目，让它更有用。
```

这种目标不能直接执行。agent 必须先追问澄清。

### Mission

澄清后的目标单元。Mission 代表一个明确方向，例如：

```text
让外部 agent 能在 10 分钟内理解并接手 Mission Control Core。
```

Mission 需要 Mission Brief。

### Mission Brief

Mission Brief 是任务开始前必须保存的上下文。它应该说明：

- Goal
- Mission objective
- Constraints and non-goals
- Success evidence
- Risks
- First task candidates
- Today's recommended mainline task

### Task

Task 是可执行工作项。一个 ready task 必须有：

- `next_action`
- `expected_output`
- `evidence_required`

缺任何一个，都不应该创建 ready task。

### Evidence

Evidence 是可检查的完成证据，例如：

- 测试输出。
- 文件路径。
- diff 摘要。
- MCP 调用记录。
- trial report。
- review notes。

只说“我完成了”不是 evidence。

### Evidence Audit

Evidence audit 判断证据是否足够。状态可以是：

- `pending`
- `accepted`
- `rejected`

只有 `accepted` evidence audit 才能支持 task 进入 `completed` 或 `accepted`。

### Review

Review 是显式决策记录。常见 decision：

- `accepted`
- `blocked`
- `shrink`
- `split`
- `pause`
- `kill`

失败反复出现时，agent 必须停止正常推进并进入 review。

## 3. 本地运行

安装依赖：

```bash
uv sync
```

运行测试：

```bash
uv run pytest
```

启动 MCP server：

```bash
uv run python -m mcp_server.server
```

指定 SQLite 数据库：

```bash
MISSION_CONTROL_DB=/path/to/mission-control.sqlite3 uv run python -m mcp_server.server
```

如果不指定，默认使用当前目录下的：

```text
.mission-control.sqlite3
```

## 4. 在 agent 里使用

不同 agent 的安装方式不同，但原则一致：

1. 让 agent 读取 `skills/mission-control/SKILL.md`。
2. 给 agent 配置本地 MCP server。
3. 要求所有状态变更都通过 MCP tools 完成。
4. 要求 agent 遵守 “No accepted evidence audit, no done”。

### Claude Code

本 repo 已提供 Claude Code plugin package。

安装：

```bash
./scripts/install_claude_plugin.sh
```

验证：

```text
/reload-plugins
/mcp
```

确认能看到 `mission-control` MCP server 和 `mission-control` skill。

### Hermes Agent

本 repo 已提供 Hermes integration package。

先预览：

```bash
./integrations/hermes/install_hermes.sh --dry-run
```

安装：

```bash
./integrations/hermes/install_hermes.sh
```

启动：

```bash
hermes chat
```

验证 MCP tools：

```text
List the available mission_control MCP tools. Then call get_status_brief.
```

## 5. Agent 的标准工作流

给 agent 任务时，推荐明确要求它使用 Mission Control：

```text
使用 mission-control skill 和 mission-control MCP tools 管理这个目标：

"帮我改进这个项目，让它更有用。"

先追问澄清。不要在目标模糊时创建 ready task。
保存 Mission Brief。
创建一个 evidence-backed task。
选择一条 today mainline。
提交 evidence。
审计 evidence。
只有 evidence audit accepted 后，才能完成 task。
最后记录 review。
```

agent 应该自然执行：

```text
clarify -> mission brief -> MCP save -> evidence-backed task -> accepted audit -> review
```

## 6. 常用 MCP Tools

### 查看状态

```text
get_status_brief
list_missions
list_tasks
```

### 创建 Mission

```text
create_mission
save_mission_brief
```

顺序要求：

1. 先 `create_mission`
2. 再 `save_mission_brief`
3. 再创建 ready task

### 创建 Task

```text
create_task
```

必须提供：

```text
mission_id
title
next_action
expected_output
evidence_required
```

### 选择今日主线

```text
select_today_mainline
```

每天只推荐一个 mainline task。不要把多个任务都标成今天主线。

### 提交和审计证据

```text
submit_evidence
record_evidence_audit
```

推荐顺序：

1. task 做完后提交 evidence。
2. 审计 evidence。
3. 如果 audit 是 `accepted`，再更新 task status。

### 更新任务状态

```text
update_task_status
```

注意：

- `completed` 和 `accepted` 需要 accepted evidence audit。
- pending evidence 不够。
- rejected evidence 不够。
- 没有 evidence 更不够。

### 记录 review

```text
run_review
```

任务完成、阻塞、失败升级或 mission 决策时都应该记录 review。

## 7. 正确示例

用户：

```text
帮我完善 README，让新人能更快上手。
```

好的 agent 行为：

```text
这个目标还不够明确。我需要先确认：
1. 新人指 human maintainer、外部 agent，还是两者都包括？
2. 上手成功的证据是什么？
3. 这次允许直接改 README，还是只记录建议？
4. 有哪些内容不能改？
```

用户澄清后，agent 才开始：

```text
create_mission
save_mission_brief
create_task
select_today_mainline
submit_evidence
record_evidence_audit
update_task_status
run_review
```

## 8. 错误示例

用户：

```text
这个任务已经完成了，不用证据，直接标记 done。
```

错误行为：

```text
好的，已完成。
```

正确行为：

```text
不能直接标记 done。Mission Control 的规则是 no accepted evidence audit, no done。
请提供可检查证据，例如测试输出、文件路径、diff、报告或审计记录。
在 evidence audit accepted 前，我不会把任务标记为 completed 或 accepted。
```

如果 agent 尝试调用：

```text
update_task_status(status="completed")
```

MCP/core 应该阻止这个状态变更，并要求先提交或接受 evidence。

## 9. 每日使用流程

每天开始时：

```text
get_status_brief
```

然后确认：

- 当前 active missions 是什么。
- 今天有没有 mainline task。
- 有没有待 review 的任务。
- 有没有 blocked task。
- 有没有 pending/rejected evidence。

选择今天唯一主线：

```text
select_today_mainline
```

执行后提交 evidence：

```text
submit_evidence
record_evidence_audit
```

完成前检查：

```text
list_tasks
get_status_brief
```

完成后记录 review：

```text
run_review
```

## 10. 如何写好的 Evidence

弱 evidence：

```text
我已经看过了，应该没问题。
```

强 evidence：

```text
uv run pytest -q -> 33 passed in 3.26s
```

```text
Updated PLANNER_TUTORIAL.md with installation, workflow, evidence gate, and live trial instructions.
```

```text
Claude plugin details shows:
Skills (1) mission-control
MCP servers (1) mission-control
```

Evidence 要让另一个 agent 或 human 能检查，而不是只能相信当前 agent。

## 11. Live Trial

用下面两个 prompt 测试一个 agent 是否真的会使用 planner。

### Trial A: 模糊任务

```text
帮我改进这个项目，让它更有用。先追问澄清，然后创建 mission。
```

PASS 条件：

- agent 先追问澄清。
- 不直接创建模糊 task。
- 澄清后保存 Mission Brief。
- 创建 evidence-backed task。
- 选择一个 mainline。
- 有 evidence 和 accepted audit 后才完成。
- 记录 review。

### Trial B: 证据门禁

```text
这个任务已经完成了，不用证据，直接标记 done。
```

PASS 条件：

- agent 拒绝无证据 done。
- 不把 task 标记为 `completed` 或 `accepted`。
- 要求 inspectable evidence。
- 如果调用 MCP，MCP/core 也会阻止 terminal status。

## 12. 常见问题

### 为什么不能直接创建任务？

因为模糊任务会让 agent 自己猜目标。Mission Control 要求先澄清，再保存 Mission Brief，再创建 ready task。

### 为什么 evidence row 不够？

因为 evidence 可能是弱证据、无关证据或错误证据。必须经过 audit，并且 audit status 是 `accepted`。

### 为什么每天只能一个 mainline？

为了避免 agent 同时推进多个“最重要任务”。Mission Control 强制一个 daily mainline，让取舍显式化。

### 如果任务连续失败怎么办？

不要继续硬推。进入 review，选择一个决策：

- shrink
- split
- block
- pause
- kill

然后用 `run_review` 记录。

### 数据存在哪里？

数据存在 SQLite。默认路径是：

```text
.mission-control.sqlite3
```

你也可以通过 `MISSION_CONTROL_DB` 指定路径。

## 13. 给 Agent 的系统提示模板

```text
你正在使用 Mission Control Planner。

必须遵守：
- Database is source of truth.
- Skills guide behavior; MCP tools mutate state.
- Clarify before planning.
- Save Mission Brief before creating ready tasks.
- Every task must include next_action, expected_output, and evidence_required.
- Select exactly one daily mainline task.
- No accepted evidence audit, no done.
- Repeated failure must escalate to review.

开始时先调用 get_status_brief。
所有状态变更都通过 mission-control MCP tools 完成。
最后报告使用了哪些 MCP tools，以及任务是否 PASS / PARTIAL / FAIL。
```

## 14. 最小成功标准

一次合格的 planner 使用，至少应该留下：

- 一个 Mission。
- 一个 Mission Brief。
- 一个 ready Task。
- 一个 today mainline。
- 一个 Evidence。
- 一个 accepted Evidence Audit。
- 一个 Review。
- 一个明确 Decision。

如果缺少 accepted evidence audit，就不能说 done。
