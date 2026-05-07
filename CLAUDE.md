# CLAUDE.md

Quick reference for DiplomaAPI development. Detailed docs in `docs/`.

---

## Working Rules

1. **One feature at a time** — Complete it fully before starting next
2. **Schema-first** — Pydantic schema → Service → Route → Tests
3. **Business logic in services** — Routes never query DB directly
4. **Type hints required** — All arguments and returns typed
5. **Async everywhere** — All I/O must be `async def` + `await`
6. **Structured logging** — Use `structlog.get_logger()`, never `print()`
7. **Test services, not routes** — Service methods must have tests
8. **JOINs not loops** — One query with JOIN, never N+1
9. **Immutable migrations** — Never edit; create new ones
10. **No hardcoded secrets** — All config from `.env`
11. **Cron hourly** — Sync via APScheduler every 60 min
12. **Specific errors** — Catch exceptions, return meaningful HTTP codes

---

## Definition of Done

Before marking a feature complete:

- ✅ Implementation matches description
- ✅ All new code has type hints
- ✅ `pytest tests/ -v` passes
- ✅ e2e tests passes
- ✅ `mypy app/ --ignore-missing-imports` passes
- ✅ Manual test in `/docs` works end-to-end
- ✅ Migration created if schema changed
- ✅ `feature_list.json` updated to `done`
- ✅ Commit message explains WHY, not WHAT
- ✅ No debug code or commented lines

---

## Quick Reference

**Understand architecture** → See [docs/architecture.md](docs/architecture.md)

**See implementation patterns** → See [docs/architecture-patterns.md](docs/architecture-patterns.md)

| Need | Link |
|------|------|
| Add endpoint | Pattern 1 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |
| Add table | Pattern 2 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |
| Sync from Gateway | Pattern 3 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |
| JOIN enrichment | Pattern 4 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |
| Date filtering | Pattern 5 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |
| Write tests | Pattern 6 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |
| Error handling | Pattern 7 in [docs/architecture-patterns.md](docs/architecture-patterns.md) |

---

## Session Checklist

**Start:**
1. Read AGENTS.md
2. Read feature_list.json
3. Run `./init.sh`
4. Read progress.md

**Work:**
1. Pick one feature
2. Follow pattern: schema → service → route → tests
3. Run `pytest tests/ -v` frequently

**Finish:**
1. `mypy app/ --ignore-missing-imports`
2. Update feature_list.json + progress.md + docs that describe the feature
3. `git commit -m "feat: description and why"`
4. `git push origin main`

---

## Commands

```bash
pytest tests/ -v                          # Run tests
mypy app/ --ignore-missing-imports        # Type check
ruff check app/                           # Lint
uvicorn app.main:app --reload             # Dev server → /docs
alembic revision -m "msg"                 # New migration
alembic upgrade head                      # Apply migrations
git log --oneline -10                     # Recent commits
```

---

**For detailed documentation, see:**
- **AGENTS.md** — Project overview, startup workflow
- **docs/architecture.md** — Three-layer design, domains, constraints
- **docs/architecture-patterns.md** — 7 implementation patterns with examples
- **feature_list.json** — Feature tracking
- **progress.md** — Session logs
