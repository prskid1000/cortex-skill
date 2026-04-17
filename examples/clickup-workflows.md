# ClickUp CLI — Working Examples

> Task management, sprints, comments, time tracking, and git integration from the terminal.

**Reference:** [references/clickup-cli.md](../references/clickup-cli.md) · install: `python scripts/healthcheck.py --install`

## Contents

- **MANAGE tasks** — `clickup` CLI workflows
  - [Read a task](#read-a-task)
  - [Search tasks](#search-tasks)
  - [List tasks in a list](#list-tasks-in-a-list)
  - [Create a task](#create-a-task)
  - [Update task status](#update-task-status)
  - [Sprint view](#sprint-view)
  - [Comments](#comments)
  - [Time tracking](#time-tracking)
  - [Custom fields](#custom-fields)
  - [Git integration (branch workflow)](#git-integration)
  - [Workspace navigation](#workspace)
  - [Development workflow pattern](#development-workflow-pattern)

## Read a Task

```bash
# View task from current git branch (auto-detects from branch name like f/CU-86abc123-foo)
clickup task view

# View by task ID (positional)
clickup task view 86abc123

# JSON output for parsing
clickup task view 86abc123 --json

# Filter specific fields with jq
clickup task view 86abc123 --json --jq '{name, status: .status.status, assignees: [.assignees[].username]}'
```

## Search Tasks

```bash
# Search across workspace (query is positional)
clickup task search "API endpoint"

# JSON output
clickup task search "deployment bug" --json

# Limit to a space or folder
clickup task search "geozone" --space "Engineering"
clickup task search "geozone" --folder "Sprint 42"

# Also search through comments
clickup task search "regression" --comments

# Recently accessed tasks
clickup task recent
```

## List Tasks in a List

```bash
clickup task list --list-id 12345
clickup task list --list-id 12345 --assignee me --status "in progress"
clickup task list --list-id 12345 --sprint "Sprint 42" --json
```

## Create a Task

```bash
# Basic task — use --list-id (not --list) and integer priority
clickup task create --name "Implement user auth" --list-id 12345

# Full task with details (priority is 1=Urgent, 2=High, 3=Normal, 4=Low)
clickup task create \
  --name "Fix invoice PDF generation" \
  --list-id 12345 \
  --priority 2 \
  --description "PDF renders blank for orders with 50+ line items" \
  --tags "bug" \
  --due-date 2026-04-20

# Add to current sprint (auto-resolves list)
clickup task create --current --name "Sprint task" --priority 3

# Create as subtask
clickup task create --list-id 12345 --name "Write tests" --parent 86abc123
```

## Update Task Status

```bash
# Signature: clickup status set <status> [task]  — both use fuzzy matching
clickup status set "in progress" 86abc123
clickup status set "review"                      # uses current branch task
clickup status set "done" 86abc123

# List available statuses
clickup status list
```

## Sprint View

```bash
# Current sprint — tasks grouped by status with assignees + priorities
clickup sprint current

# JSON for automation
clickup sprint current --json

# List all sprints
clickup sprint list
```

## Comments

```bash
# Signature: clickup comment add [TASK] [BODY]  — both positional
clickup comment add 86abc123 "Backend MR: https://gitlab.com/mposweb/java-code/-/merge_requests/456"

# Mention a teammate — embed @Name inside the body (resolved via member list)
clickup comment add 86abc123 "Hey @Isaac, ready for review"

# Use "" for TASK to auto-detect from branch
clickup comment add "" "Deployed to staging"

# Compose in $EDITOR
clickup comment add --editor

# Read comments
clickup comment list 86abc123
```

## Time Tracking

```bash
# Log time (task ID is positional and optional — auto-detected from branch)
clickup task time log 86abc123 --duration 2h30m --description "Backend implementation"
clickup task time log --duration 45m --date 2026-04-04 --billable

# View time entries on a task
clickup task time list 86abc123

# Timesheet across a date range
clickup task time list --start-date 2026-02-01 --end-date 2026-02-28 --assignee me
clickup task time list --start-date 2026-02-01 --end-date 2026-02-28 --assignee all \
    --jq '[.[] | {task: .task.name, hrs: (.duration | tonumber / 3600000)}]'
```

## Custom Fields

```bash
# List available fields
clickup field list --json

# Set via task edit
clickup task edit 86abc123 --field "Environment=staging"
clickup task edit 86abc123 --field "Environment=production" --field "QA Passed=true"

# Clear a custom field
clickup task edit 86abc123 --clear-field "Environment"
```

## Git Integration

```bash
# Link current PR to task (auto-detects both from branch + gh CLI)
clickup link pr

# Link specific PR (PR number is positional)
clickup link pr 456 --repo mposweb/java-code --task 86abc123

# Link current branch
clickup link branch --task 86abc123

# Link commit (SHA is positional, HEAD if omitted)
clickup link commit
clickup link commit a1b2c3d --task 86abc123 --repo mposweb/java-code

# Re-sync known git refs
clickup link sync
```

## Workspace

```bash
# Team members — useful for finding user IDs for --assignee
clickup member list
clickup member list --json --jq '.[] | {id, username, email}'

# Tags
clickup tag list

# Notifications/mentions
clickup inbox
```

## Development Workflow Pattern

```bash
# 1. Check sprint tasks
clickup sprint current

# 2. Pick a task and view details
clickup task view 86abc123 --json

# 3. Create branch (embed task ID for auto-detection)
git checkout -b f/CU-86abc123-invoice-fix

# 4. ... implement changes ...

# 5. Mark in progress (auto-detects task from branch)
clickup status set "in progress"

# 6. Create MR and link
git push -u origin f/CU-86abc123-invoice-fix
glab mr create --title "fix(invoice): PDF generation for large orders"
clickup link pr               # or: clickup link branch
clickup comment add "" "MR created: https://gitlab.com/..."

# 7. Mark for review
clickup status set "review"

# 8. Log time
clickup task time log --duration 3h --description "Implementation + testing"
```
