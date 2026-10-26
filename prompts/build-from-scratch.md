# Prompt: build the observatory from scratch

The original prompt this repo came from. Paste it into Claude Code or Codex to regenerate the analyzer,
dashboard and HARNESS.md without the skill. To reuse the existing code instead, use
[`weekly-review.md`](weekly-review.md).

```text
<pasted_content id="73b9">
Build me a Langfuse-style observability dashboard from my own AI coding sessions for the last 7 days.

SOURCES (read locally, read-only):
- Claude Code: ~/.claude/projects/**/*.jsonl
- Codex: ~/.codex/sessions/**/*.jsonl (and ~/.codex/history.jsonl)
Never print secrets, keys or full prompt text. Snippets max 10 words, with keys, paths, URLs and long ids stripped.

STEP 1. Write a stdlib-only Python script that computes, per tool:
- sessions per day, user prompts, tool calls by tool name, failed tool calls by tool and error type
- models used, tokens (input, output, cache read/write) per model per day
- tool-call latency p50/p95, overall and per tool; session length p50/p95
- top sessions by tokens, longest sessions, retries (same tool call repeated after an error)
- prompts clustered into task types (build, debug, deploy, research, writing, UI, review, other)
- sessions grouped by project (working directory), with subagent runs flagged
If a log doesn't record something, write "not logged". Never invent numbers.
Save the result as harness-summary.json.

STEP 2. Render a single-file dashboard.html (dark, animated numbers and charts):
- Summary strip: total tool calls, prompts, error rate, tokens, p95 latency
- Traces table: one row per session (tool, project, start, duration, prompts, tool calls, errors, tokens, model); search, filter by tool, sort, toggle to hide subagent runs
- Trace detail: click a session to see a waterfall of its turns and tool calls with ok/error and duration
- Sessions by project, tokens over time by model, a model table (tokens, error rate)
- Latency view per tool, and an error explorer grouped by tool and error type
- Heuristic scores (tool success rate, retries, per-session health), clearly labeled "heuristic"
Cap embedded traces at the top 200 sessions by tokens if the file gets too big.

STEP 3. From the data, write HARNESS.md proposing changes to CLAUDE.md / AGENTS.md:
- Model routing: which model for which task type, based on what I used and what failed
- Tools: keep (high use, low failure), fix (high failure), cut (rarely used)
- Skills: one for every task type I repeated 3+ times, with a trigger line and steps
- Guardrails: my top 3 failure patterns and a check that prevents each
- Budget: my top 5 token sinks and one change that would cut each
Cite the sessions behind each suggestion.

STEP 4. Show me the 5 headline numbers and the proposed diff before changing any config. I'll review weekly and change only what the data shows.
```
