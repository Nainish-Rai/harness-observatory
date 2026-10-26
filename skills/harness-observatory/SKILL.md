---
name: harness-observatory
description: Build a local Langfuse-style observability dashboard from your own Claude Code and Codex session logs, and draft evidence-backed CLAUDE.md/AGENTS.md changes from it. Use for "harness dashboard", "observability for my agent sessions", "how did my agents do this week", or a weekly harness review.
---

# Harness observatory

Reads `~/.claude/projects/**/*.jsonl` and `~/.codex/sessions/**/*.jsonl` (plus `~/.codex/history.jsonl` and
`~/.codex/session_index.jsonl`) **read-only**, writes `harness-summary.json`, and renders it into a single-file
`dashboard.html`. Paths below are relative to this skill's base directory. Python 3.9+, stdlib only.

## Ground rules

- **Evidence only.** Every number comes from `harness-summary.json`. Anything the logs do not record is
  written as `not logged`.
- **Redacted.** Snippets are at most 10 words with keys, paths, URLs, emails and long ids stripped
  (`snippet()` in the analyzer). Quote titles and snippets from the JSON, never from raw logs.
- **Local.** `dashboard.html` and `harness-summary.json` hold the person's session data: they stay on disk,
  out of git (see `.gitignore`), and are never published.
- **Proposal before change.** Config edits wait for the person's explicit go-ahead on a shown diff.

## Steps

1. **Collect.** In the person's chosen output folder:
   `python3 -I <skill>/scripts/harness_summary.py [--days 7] [--max-traces 200]`.
   Done when it prints `sessions N (+M subagent runs), prompts …, tool calls …` and the JSON exists.
2. **Render.** `python3 -I <skill>/scripts/render_dashboard.py` (reads `harness-summary.json`, writes
   `dashboard.html`, trims embedded traces past `--max-mb 8`). Done when it prints the size and trace count.
3. **Verify.** Open `dashboard.html`. Every tab (Overview, Traces, Latency, Errors, Scores) shows data, the
   tool switch re-renders, a trace row opens the waterfall drawer. If you changed the template, also run
   `python3 -I <skill>/scripts/check_tokens.py <skill>/assets/dashboard.template.html` and expect `0 finding(s)`.
4. **Report.** Give the 5 headline numbers from `headline` (tool calls, user prompts, error rate, tokens,
   p95 tool latency) and the path to the dashboard.

## Weekly review (when asked for proposals)

Write `HARNESS.md` beside the JSON, every claim citing session ids (first 8 chars):

- **Model routing**: error rate by task type × model; say when the comparison is thin.
- **Tools**: keep / fix / cut, with call counts, failure rates and main error types.
- **Skills**: one per task type repeated in 3+ sessions, each with a trigger line and steps; route to an
  existing skill when one covers it.
- **Guardrails**: the top 3 failure patterns, each with a one-line check.
- **Budget**: the top 5 token sinks (session + its subagents), with LLM calls and average context per call.
- **Proposed diff**: against the files that are the source of the person's CLAUDE.md / AGENTS.md (if those
  are rendered or symlinked, diff the source). Mark it "not applied".

Then show the 5 headline numbers and the diff, and stop: the person decides what changes.

## Reading the data

- Task types are a keyword heuristic (`classify()`); health is `60% tool success + 20% (1 − retries/5) +
  20% (1 − interrupts/3)`. Label both "heuristic".
- Exit-code errors include benign ones (`rg`/`grep` with no match exits 1).
- Claude Code tool latency includes time spent on permission prompts.
- Cache reads usually dominate tokens, so cost follows context size × LLM calls.
- A session still running during the analysis keeps growing; re-run before quoting final numbers.
