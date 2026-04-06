# Claude Code Hooks

This directory contains automated hooks for project maintenance.

## Auto-Commit Hook

### Purpose
Automatically tracks and commits project changes every hour.

### Schedule
- **Frequency**: Every hour at minute 0
- **Cron expression**: `0 * * * *`

### Commit Message Format
All auto-commits use **English** messages following Conventional Commits:

```
<type>: <description>
```

Examples:
- `feat: Add 3 file(s)`
- `refactor: Update 5 file(s)`
- `chore: Remove 2 file(s), Add 1 file(s)`

### Commit Types
| Change Pattern | Type |
|---------------|------|
| More additions | `feat` |
| More modifications | `refactor` |
| More deletions | `chore` |
| Mixed/balanced | `chore` |

### Manual Execution
```bash
uv run python .claude/hooks/auto_commit.py
```

### Setup (Optional - System Cron)
To enable system-level scheduling:

**Linux/Mac (crontab -e):**
```bash
0 * * * * cd /path/to/multi-agent-design-patterns && uv run python .claude/hooks/auto_commit.py >> .claude/hooks/auto_commit.log 2>&1
```

**Windows (Task Scheduler):**
- Create task to run hourly
- Action: `uv run python E:\1_LLM_PROJECT\multi-agent-design-patterns\.claude\hooks\auto_commit.py`

### Notes
- Auto-commit only stages and commits locally
- Manual `git push` required to sync with remote
- Designed to avoid merge conflicts by not auto-pushing
