# ClickUp CLI — Command Reference

> Terminal tool for ClickUp tasks, sprints, comments, time tracking, and git integration.

**Related:** [examples/clickup-workflows.md](../examples/clickup-workflows.md) | [setup.md](setup.md)

---

## Setup

```bash
# Auth with API token (interactive prompt)
clickup auth login

# Non-interactive (CI/CD, scripts)
clickup auth login --with-token

# Select default workspace/space
clickup space select
```

## Output Flags (all commands)

| Flag | Description |
|------|-------------|
| `--json` | Structured JSON output (for parsing/automation) |
| `--jq <expr>` | Inline jq filtering on JSON output |
| `--template <tmpl>` | Go template formatting |
| `--format text` | Human-readable text (default) |

---

## Task Management

### `task view` — View task details

```bash
clickup task view                          # from current git branch (auto-detect)
clickup task view --task <TASK_ID>         # by task ID
clickup task view --task <TASK_ID> --json  # JSON output
```

Returns: name, status, priority, assignees, watchers, tags, dates, points, time tracking, location, dependencies, checklists, custom fields, URL, description.

### `task create` — Create a task

```bash
clickup task create --name "Task title" --list <LIST_ID>
clickup task create --name "Bug fix" --list <LIST_ID> --priority urgent --assignee "user@email.com"
clickup task create --name "Sprint task" --current    # add to active sprint
```

| Flag | Description |
|------|-------------|
| `--name` | Task name (required) |
| `--list` | Target list ID |
| `--current` | Add to current/active sprint |
| `--priority` | urgent, high, normal, low |
| `--assignee` | Assignee email or name |
| `--description` | Task description |
| `--tag` | Tag name |
| `--points` | Story points |
| `--due` | Due date |
| `--time-estimate` | Time estimate |

### `task edit` — Modify a task

```bash
clickup task edit --task <TASK_ID> --name "New name"
clickup task edit --task <TASK_ID> --priority high --assignee "user@email.com"
```

### `task search` — Search tasks

```bash
clickup task search --query "API endpoint"
clickup task search --query "bug" --json
```

### `task recent` — Recently accessed tasks

```bash
clickup task recent
clickup task recent --json
```

---

## Status Management

### `status set` — Change task status (fuzzy matching)

```bash
clickup status set --task <TASK_ID> --status "in progress"
clickup status set --status "review"          # from current branch
clickup status set --status "done"            # "done" fuzzy-matches "Done", "DONE", etc.
```

### `status list` — Available statuses

```bash
clickup status list
clickup status list --json
```

---

## Sprint Management

### `sprint current` — Active sprint tasks

```bash
clickup sprint current                # tasks grouped by status with assignees + priorities
clickup sprint current --json
```

### `sprint list` — All sprints

```bash
clickup sprint list
```

---

## Comments

### `comment add` — Post comment

```bash
clickup comment add --task <TASK_ID> --body "MR ready for review: https://gitlab.com/..."
clickup comment add --body "Deployed to staging" --mention "user@email.com"
```

| Flag | Description |
|------|-------------|
| `--task` | Task ID (or auto-detect from branch) |
| `--body` | Comment text |
| `--mention` | @mention a user |

### `comment list` — View comments

```bash
clickup comment list --task <TASK_ID>
clickup comment list --json
```

---

## Time Tracking

### `task time log` — Record time

```bash
clickup task time log --task <TASK_ID> --duration "2h30m" --description "Backend implementation"
```

### `task time list` — View time entries

```bash
clickup task time list --task <TASK_ID>
clickup task time list --json
```

---

## Custom Fields

### `field list` — List available custom fields

```bash
clickup field list
clickup field list --json
```

### Set/clear custom fields (via `task edit`)

Supports: text, dropdown, labels, dates, URLs, and more.

---

## Git Integration

### `link pr` — Link GitHub PR to task

```bash
clickup link pr                           # auto-detect from current branch + open PR
clickup link pr --task <TASK_ID> --repo owner/repo --pr 123
```

### `link branch` — Link branch to task

```bash
clickup link branch
clickup link branch --task <TASK_ID> --branch "f/feature-name"
```

### `link commit` — Link commit to task

```bash
clickup link commit --task <TASK_ID> --sha abc123
```

### `link sync` — Sync all git refs

```bash
clickup link sync
```

---

## Workspace

### `member list` — Team members

```bash
clickup member list
clickup member list --json
```

### `tag list` — Available tags

```bash
clickup tag list
```

### `inbox` — Recent mentions/notifications

```bash
clickup inbox
```

### `space select` — Switch workspace/space

```bash
clickup space select
```
