# ClickUp CLI — Command Reference

> Terminal tool for ClickUp tasks, sprints, comments, time tracking, and git integration.

**Related:** [examples/clickup-workflows.md](../examples/clickup-workflows.md) · install: `python scripts/healthcheck.py --install` (clickup binary itself is a manual GitHub release download; see healthcheck hints)

## Contents

- **MANAGE tasks** — `clickup` CLI
  - [Conventions (positional IDs, priorities, dates)](#conventions-important)
  - [Setup & authentication](#setup)
  - [Output flags (JSON, jq, templates)](#output-flags-most-commands)
  - [Task management (view, create, edit, search, bulk)](#task-management)
  - [Status management (transitions, list statuses)](#status-management)
  - [Sprint management (current sprint, sprint view)](#sprint-management)
  - [Comments (add, list, mention teammates)](#comments)
  - [Time tracking (start, stop, log, list)](#time-tracking)
  - [Custom fields (discover, set, clear)](#custom-fields)
  - [Git integration (PR / branch / commit linking)](#git-integration)
  - [Checklists, dependencies, tags](#checklists-dependencies-tags-on-tasks)
  - [Workspace (spaces, lists, members)](#workspace)
  - [Misc / less-used commands](#more)

## Conventions (important)

- **Task IDs are positional**, not a `--task` flag. `clickup task view <id>`, `clickup comment add <id> "body"`, `clickup task edit <id> --name ...`. If you omit the ID, most commands auto-detect it from the current git branch name (e.g. `f/CU-86abc123-foo`).
- **Priority is an integer**: `1=Urgent, 2=High, 3=Normal, 4=Low`. Not a string.
- **Dates are `YYYY-MM-DD`**: use `--due-date`, `--start-date`, not `--due`.
- **Lists use `--list-id`** (not `--list`).
- **Tags use `--tags`** (plural, comma-separated or repeated).
- **Mentions** go inside the comment body as `@Username` — the CLI resolves them against `clickup member list` (case-insensitive). There is no `--mention` flag.
- Verify any command's exact flags with `clickup <cmd> --help` — the CLI evolves.

## Setup

```bash
# Auth with API token (interactive prompt)
clickup auth login

# Non-interactive (CI/CD, scripts)
clickup auth login --with-token

# Select default workspace/space
clickup space select
```

## Output Flags (most commands)

| Flag | Description |
|------|-------------|
| `--json` | Structured JSON output (for parsing/automation) |
| `--jq <expr>` | Inline jq filtering on JSON output |
| `--template <tmpl>` | Go template formatting |

---

## Task Management

### `task view` — View task details

```bash
clickup task view                       # auto-detect from current git branch
clickup task view 86a3xrwkp             # by task ID (positional)
clickup task view 86a3xrwkp --json      # JSON output (includes subtasks with IDs)
clickup task view 86a3xrwkp --jq '.subtasks[].id'   # extract subtask IDs
```

Returns: name, status, priority, assignees, watchers, tags, dates, points, time tracking, location, dependencies, checklists, custom fields, URL, description.

### `task create` — Create a task

```bash
# In current sprint (auto-resolves list)
clickup task create --current --name "[Bug] Auth — Fix login timeout (API)" --priority 2

# With explicit list ID
clickup task create --list-id 12345 --name "Write tests" --priority 3

# With custom field and due date
clickup task create --current --name "[Feature] Deploy to staging" \
    --field "Environment=staging" --due-date 2026-03-01

# As subtask of another task
clickup task create --list-id 12345 --name "Write tests" --parent 86abc123

# Bulk create from JSON file (array of task objects)
clickup task create --current --from-file tasks.json
```

| Flag | Description |
|------|-------------|
| `--name` | Task name |
| `--list-id` | Target list ID |
| `--current` | Create in the current sprint (auto-resolves list) |
| `--priority` | Integer: 1=Urgent, 2=High, 3=Normal, 4=Low |
| `--assignee` | Assignee user ID(s) — repeatable |
| `--description` / `--markdown-description` | Task description |
| `--tags` | Tag(s), comma-separated or repeated |
| `--points` | Sprint/story points |
| `--due-date` / `--start-date` | YYYY-MM-DD |
| `--time-estimate` | e.g. `2h`, `30m`, `1h30m` |
| `--field "Name=value"` | Set a custom field (repeatable) |
| `--parent` | Parent task ID (creates a subtask) |
| `--type` | 0=task, 1=milestone |
| `--from-file` | JSON file of task objects for bulk create |

### `task edit` — Modify a task (or many)

```bash
# Auto-detect task from branch
clickup task edit --status "in progress" --priority 2

# Specific task
clickup task edit 86abc123 --name "New title"
clickup task edit 86abc123 --field "Environment=production" --due-date 2026-03-01
clickup task edit 86abc123 --clear-field "Environment"

# Bulk edit
clickup task edit 86abc1 86abc2 86abc3 --status "Closed"

# Tag ops (add without clobbering, or remove)
clickup task edit 86abc123 --add-tags new-feature
clickup task edit 86abc123 --remove-tags fix
```

### `task search` — Search by name/description

```bash
clickup task search "api endpoint"                    # query is positional
clickup task search "bug" --json
clickup task search "geozone" --space "Engineering"   # limit to a space
clickup task search "geozone" --folder "Sprint 42"    # limit to a folder
clickup task search "geozone" --comments              # also search comments
clickup task search "geozone" --pick                  # interactive picker
```

### `task list` — List tasks in a list

```bash
clickup task list --list-id 12345
clickup task list --list-id 12345 --assignee me --status "in progress"
clickup task list --list-id 12345 --sprint "Sprint 42" --json
```

### `task recent` / `task activity`

```bash
clickup task recent                     # recently accessed
clickup task activity 86abc123          # full history + comments for a task
```

### `task delete` / `task list-add` / `task list-remove`

```bash
clickup task delete 86abc123
clickup task list-add 86abc123 --list-id 67890
clickup task list-remove 86abc123 --list-id 67890
```

---

## Status Management

### `status set` — Change status (fuzzy matching)

```bash
clickup status set "in progress"               # auto-detect task from branch
clickup status set "done" 86abc123             # <status> then optional <task>
clickup status set "prog" 86abc123             # fuzzy match allowed
```

### `status list`

```bash
clickup status list
clickup status list --json
```

---

## Sprint Management

```bash
clickup sprint current           # tasks in the active sprint, grouped by status
clickup sprint current --json
clickup sprint list              # all sprints
```

---

## Comments

### `comment add` — Post a comment

```bash
# Both arguments are positional: [TASK] [BODY]
clickup comment add 86abc123 "MR ready for review: https://gitlab.com/..."

# Use "" for TASK to auto-detect from branch
clickup comment add "" "Fixed the login bug"

# Mention a teammate — embed @Name in the body (resolved against member list)
clickup comment add 86abc123 "Hey @Isaac can you review this?"

# Open $EDITOR to compose
clickup comment add --editor
```

### `comment list` / `edit` / `reply` / `delete`

```bash
clickup comment list 86abc123
clickup comment list 86abc123 --json
clickup comment edit <comment-id> "new body"
clickup comment reply <comment-id> "reply text"
clickup comment delete <comment-id>
```

---

## Time Tracking

### `task time log` — Record time

```bash
# Task is positional (auto-detected from branch if omitted)
clickup task time log 86a3xrwkp --duration 2h
clickup task time log --duration 1h30m --description "Implemented auth flow"
clickup task time log 86a3xrwkp --duration 45m --date 2026-01-15
clickup task time log --duration 3h --billable
```

### `task time list` — View entries / timesheet

```bash
clickup task time list 86a3xrwkp
clickup task time list --start-date 2026-02-01 --end-date 2026-02-28 --assignee all
clickup task time list --start-date 2026-02-01 --end-date 2026-02-28 --assignee 54695018
clickup task time list --start-date 2026-02-01 --end-date 2026-02-28 \
    --jq '[.[] | {task: .task.name, hrs: (.duration | tonumber / 3600000)}]'
```

---

## Custom Fields

```bash
# Discover fields
clickup field list
clickup field list --json

# Set / clear values via task edit
clickup task edit 86abc123 --field "Environment=staging"
clickup task edit 86abc123 --clear-field "Environment"
```

Supports text, dropdown, labels, dates, URLs, numbers, and more.

---

## Git Integration

### `link pr` — Link a GitHub PR to a task

```bash
# Auto-detect both task (from branch) and PR (via gh CLI)
clickup link pr

# Specific PR number (positional)
clickup link pr 42

# Specific PR in another repo, explicit task
clickup link pr 1109 --repo owner/repo --task 86d1rn980
```

### `link branch` — Link current branch to a task

```bash
clickup link branch                       # auto-detect task from branch name
clickup link branch --task CU-abc123
```

### `link commit` — Link a commit (SHA is positional)

```bash
clickup link commit                        # HEAD commit
clickup link commit a1b2c3d
clickup link commit a1b2c3d --task CU-abc123 --repo owner/repo
```

### `link sync`

```bash
clickup link sync                          # re-sync known git refs
```

---

## Checklists, Dependencies, Tags (on tasks)

```bash
clickup task checklist <task-id> ...       # see `--help` for sub-ops
clickup task dependency <task-id> ...      # see `--help` for sub-ops
clickup tag list
```

---

## Workspace

```bash
clickup member list                  # workspace members (get user IDs here)
clickup member list --json --jq '.[] | select(.username=="Alice") | .id'

clickup inbox                        # recent @mentions
clickup space select                 # switch workspace/space
```

---

## More

This reference covers the common surface. Other available groups: `clickup field`, `clickup space`, `clickup status`, `clickup sprint`, `clickup tag`. For anything not listed, run `clickup <group> --help` — the CLI's help is authoritative.
