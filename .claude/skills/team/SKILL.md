---
name: team
description: Run the whole agent team in one word. "/team" alone = full health check (tester + reviewer in parallel, leader verifies and reports). "/team <task>" = builder does the task, then tester and reviewer check it, then the leader reports. Use when the owner types /team or says "run the team".
---

# /team — run the whole team

You (the main session) are the **leader**. Read `CLAUDE.md` section 2a first: its rules bind every agent.
The agents are in `.claude/agents/`: `builder`, `tester`, `reviewer`. If they cannot be loaded by name
(the session started before they existed), use a `general-purpose` agent and tell it to first read
`.claude/agents/<role>.md` and act exactly as that role.

## Mode A — `/team` with no task: health check
1. Start `tester` and `reviewer` **at the same time** (both in one message, both read-only).
   - tester: backend tests, frontend tests, frontend build; exact counts.
   - reviewer: review uncommitted changes (`git diff`) or, if git is clean, the last 3 commits; plus the safety checks: HARD_LIMITS, no live order path, `scanner.QUALIFIED`, no committed secrets, 127.0.0.1 only, news calendar coverage.
2. When both report, **verify every problem yourself** (read the file:line) before telling the owner. Drop anything that is not real and say why.
3. Report to the owner in simple English: headline "All good" or "Needs attention", a small table (Tests / Safety / Problems), and the problems most serious first.
4. Do not fix anything in this mode. Offer the fix as a question.

## Mode B — `/team <task>`: do a task
1. **Freeze check first.** If the task is a weekly strategy change, a new feature, a second new idea, or anything section 2a forbids, stop and explain why. Do not start the builder.
2. If the task is small (one or two lines), do it yourself instead of the builder, and say so.
3. Otherwise give the task to `builder`. Wait for its report.
4. Then start `tester` and `reviewer` at the same time on the builder's change.
5. If either finds a real problem, send it back to `builder` once with the exact problem, then re-run `tester`. After 2 rounds without success, stop and report to the owner.
6. Report: what changed (files), test results, review result, and what is not done.

## Always
- No agent commits or pushes. Only the leader does, and only when the owner says so in this conversation.
- Never touch `backend/.env`, risk limits, `scanner.QUALIFIED`, the 2025+ data, or add a live order path.
- End with one clear question if the owner has a decision to make (for example "Commit and push?").
