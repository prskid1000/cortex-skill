# ClickUp CLI — Working Examples

> Task management, sprints, comments, time tracking, and git integration from the terminal.

**Reference:** [references/clickup-cli.md](../references/clickup-cli.md)

---

## Read a Task

```bash
# View task from current git branch (auto-detects task ID from branch name)
clickup task view

# View by task ID
clickup task view --task 86abc123

# JSON output for parsing
clickup task view --task 86abc123 --json

# Filter specific fields with jq
clickup task view --task 86abc123 --json --jq '.name, .status, .assignees'
```

## Search Tasks

```bash
# Search across workspace
clickup task search --query "API endpoint"

# JSON output
clickup task search --query "deployment bug" --json

# Recently accessed tasks
clickup task recent
```

## Create a Task

```bash
# Basic task
clickup task create --name "Implement user auth" --list 12345

# Full task with details
clickup task create \
  --name "Fix invoice PDF generation" \
  --list 12345 \
  --priority high \
  --assignee "prith@example.com" \
  --description "PDF renders blank for orders with 50+ line items" \
  --tag "bug"

# Add to current sprint
clickup task create --name "Sprint task" --current
```

## Update Task Status

```bash
# Fuzzy matching — "review" matches "Code Review", "In Review", etc.
clickup status set --task 86abc123 --status "in progress"
clickup status set --status "review"          # uses current branch task
clickup status set --status "done"

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
# Add MR link as comment
clickup comment add --task 86abc123 --body "Backend MR: https://gitlab.com/mposweb/java-code/-/merge_requests/456"

# Add comment with @mention
clickup comment add --task 86abc123 --body "Ready for review" --mention "reviewer@example.com"

# Read comments
clickup comment list --task 86abc123
```

## Time Tracking

```bash
# Log time spent
clickup task time log --task 86abc123 --duration "2h30m" --description "Backend implementation"

# View time entries
clickup task time list --task 86abc123
```

## Custom Fields

```bash
# List available fields
clickup field list --json

# Set via task edit (text, dropdown, labels, dates, URLs)
clickup task edit --task 86abc123 --field "Environment=staging"
```

## Git Integration

```bash
# Link current PR to task (auto-detect from branch + open PR)
clickup link pr

# Link specific PR
clickup link pr --task 86abc123 --repo mposweb/java-code --pr 456

# Link branch
clickup link branch --task 86abc123 --branch "f/invoice-fix"

# Link commit
clickup link commit --task 86abc123 --sha abc1234

# Sync all git refs
clickup link sync
```

## Workspace

```bash
# Team members
clickup member list

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
clickup task view --task 86abc123

# 3. Create branch (task ID in branch name for auto-detection)
git checkout -b f/86abc123-invoice-fix

# 4. ... implement changes ...

# 5. Update task status
clickup status set --status "in progress"

# 6. Create MR and link
git push -u origin f/86abc123-invoice-fix
glab mr create --title "fix(invoice): PDF generation for large orders"
clickup link pr
clickup comment add --body "MR created: <url>"

# 7. Mark for review
clickup status set --status "review"

# 8. Log time
clickup task time log --duration "3h" --description "Implementation + testing"
```
