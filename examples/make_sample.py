#!/usr/bin/env python3
"""Generate a fully synthetic harness-summary.json for the dashboard demo (stdlib only).

    python3 -I examples/make_sample.py [--out examples/sample-summary.json] [--seed 2026]

Nothing is read from real logs. Sessions, projects, prompts, titles and timings are invented
here with a fixed seed, then passed through the analyzer's own per-session and aggregate code
(finish_session and summarise in harness_summary.py), so the output schema matches a real run.
The window always ends on 2026-10-26 20:00 UTC, so the file is identical on every machine.
"""
import os
import time

os.environ["TZ"] = "UTC"  # day buckets and ISO strings must not depend on the machine running this
time.tzset()

import argparse  # noqa: E402
import collections  # noqa: E402
import datetime as dt  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import random  # noqa: E402
import sys  # noqa: E402

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "harness-observatory", "scripts"))
import harness_summary as hs  # noqa: E402

hs.HOME = "/home/demo"  # project_name() strips this prefix; no real home directory is involved
UNTIL = dt.datetime(2026, 10, 26, 20, 0, 0, tzinfo=dt.timezone.utc).timestamp()
SINCE = UNTIL - 7 * 86400
DAY0 = UNTIL - 6 * 86400 - 20 * 3600  # 2026-10-20 00:00 UTC

SUB_RUNS = 50
CLAUDE_MODELS = ["claude-opus-5-5", "claude-sonnet-5-5"]
CODEX_MODELS = ["gpt-6-astra", "gpt-6.1-sol"]

# (project, title, tool) -- every name here is invented
SESSIONS = [
    ("acme/billing-api", "Fix proration rounding in annual plan upgrades", "claude-code"),
    ("acme/web-app", "Fix checkout retry loop on slow networks", "claude-code"),
    ("acme/web-app", "Responsive layout for account settings page", "claude-code"),
    ("acme/web-app", "Add dark mode toggle to the header", "codex"),
    ("acme/web-app", "Debug hydration mismatch on product page", "claude-code"),
    ("acme/web-app", "Migrate cart state to the new store", "codex"),
    ("acme/web-app", "Speed up the search results page", "claude-code"),
    ("acme/web-app", "Review the open PR for the onboarding flow", "claude-code"),
    ("acme/web-app", "Audit bundle size after the chart upgrade", "codex"),
    ("acme/web-app", "Research feature flag vendors", "claude-code"),
    ("acme/billing-api", "Add idempotency keys to invoice webhooks", "claude-code"),
    ("acme/billing-api", "Investigate duplicate charge reports", "claude-code"),
    ("acme/billing-api", "Refactor tax calculation into its own module", "codex"),
    ("acme/billing-api", "Rate limit the public pricing endpoint", "codex"),
    ("acme/billing-api", "Backfill missing invoice line items", "claude-code"),
    ("acme/billing-api", "Explain how dunning retries are scheduled", "claude-code"),
    ("acme/billing-api", "Write the migration for plan metadata", "codex"),
    ("acme/billing-api", "Sanity check the refund report numbers", "claude-code"),
    ("demo/docs-site", "Draft quickstart guide for the CLI", "claude-code"),
    ("demo/docs-site", "Fix broken anchors in the API reference", "codex"),
    ("demo/docs-site", "Rewrite the authentication overview page", "claude-code"),
    ("demo/docs-site", "Add search to the docs sidebar", "codex"),
    ("demo/docs-site", "Summarise the changelog for the October release", "claude-code"),
    ("demo/docs-site", "Update screenshots in the getting started tour", "codex"),
    ("demo/infra", "Roll out staging cluster node upgrade", "claude-code"),
    ("demo/infra", "Terraform plan drift in the network module", "codex"),
    ("demo/infra", "Ship the release pipeline to production", "claude-code"),
    ("demo/infra", "Tune autoscaling for the worker pool", "codex"),
    ("demo/infra", "Rotate staging database credentials safely", "claude-code"),
    ("demo/infra", "Investigate slow container cold starts", "claude-code"),
    ("demo/infra", "Set up alerts for queue backlog", "codex"),
    ("acme/mobile-app", "Crash on resume after background refresh", "claude-code"),
    ("acme/mobile-app", "Add offline banner to the feed", "codex"),
    ("acme/mobile-app", "Upgrade the navigation library", "claude-code"),
    ("acme/mobile-app", "Fix flaky login test on Android", "codex"),
    ("demo/data-pipeline", "Nightly import job fails on empty files", "claude-code"),
    ("demo/data-pipeline", "Compare queue options for event ingestion", "claude-code"),
    ("demo/data-pipeline", "Write data quality checks for orders", "codex"),
    ("demo/data-pipeline", "Add retries to the export task", "codex"),
    ("demo/data-pipeline", "Profile memory use in the join step", "claude-code"),
]
OPENERS = ["", ", tests should still pass", " and explain the approach first", ", keep the change small",
           ", check how it works today before editing", " and add a test for it"]
FOLLOW = [
    "ok continue", "yes go ahead", "that test still fails, check the error output", "run the full suite again",
    "can you also update the docs page", "looks good, open a PR", "why did the build break after that change",
    "keep going", "compare that with the old behaviour", "add a test for the empty case", "deploy it to staging",
    "review the diff before we merge", "make the button spacing match the design", "write a short summary for the ticket",
    "lgtm", "explain what changed in plain words", "check the logs for the failing job",
    "revert the last edit, it broke the layout", "what is the best way to handle the timeout here",
    "investigate why the numbers differ between environments",
]
SLASH = ["/review the pending changes", "/compact"]
CLAUDE_AGENTS = [
    ("Find all callers of the pricing helper", "Explore"), ("Review the migration for data loss", "code-reviewer"),
    ("Explore how sessions are stored", "Explore"), ("Audit the docs for broken links", "general-purpose"),
    ("Check test coverage for webhooks", "general-purpose"), ("Draft the changelog entry", "general-purpose"),
    ("Search for unused feature flags", "Explore"), ("Map the deploy pipeline stages", "Plan"),
    ("Reproduce the failing checkout test", "general-purpose"), ("Compare two caching approaches", "Plan"),
    ("Collect slow queries from the test run", "Explore"), ("Verify the fix against the spec", "code-reviewer"),
]
CODEX_AGENTS = [
    "Run the test suite and summarise the failures", "Inspect the plan output for unexpected drift",
    "Search the repo for the deprecated client", "Check which screens use the old banner",
    "List endpoints missing rate limits", "Profile the slowest test files",
]

CLAUDE_TOOLS = {"Bash": 30, "Read": 24, "Edit": 14, "Grep": 10, "Glob": 4, "Write": 4, "TodoWrite": 2, "WebFetch": 2,
                "WebSearch": 1.5, "mcp__tracker__get_issue": 1.5, "mcp__docs__search": 1, "ToolSearch": 1}
CLAUDE_SUB_TOOLS = {"Read": 35, "Grep": 25, "Glob": 10, "Bash": 20, "WebFetch": 4, "WebSearch": 3, "Edit": 3}
CODEX_TOOLS = {"shell": 55, "apply_patch": 18, "mcp:tracker.search_issues": 5, "mcp:docs.lookup": 4, "view_image": 2, "update_plan": 4}
CODEX_SUB_TOOLS = {"shell": 70, "apply_patch": 6, "mcp:docs.lookup": 4, "view_image": 2}

LAT = {  # median seconds, lognormal sigma
    "Bash": (2.2, 1.3), "Read": (0.06, 0.6), "Grep": (0.22, 0.7), "Glob": (0.09, 0.6), "Edit": (0.12, 0.8),
    "Write": (0.15, 0.7), "TodoWrite": (0.03, 0.4), "WebFetch": (3.2, 0.7), "WebSearch": (4.5, 0.5),
    "mcp__tracker__get_issue": (1.1, 0.6), "mcp__docs__search": (1.6, 0.6), "ToolSearch": (0.04, 0.5),
    "shell": (1.6, 1.3), "apply_patch": (0.25, 0.6), "mcp:tracker.search_issues": (1.3, 0.6),
    "mcp:docs.lookup": (1.8, 0.6), "view_image": (0.08, 0.4), "update_plan": (0.02, 0.4),
}
ERR = {  # failure probability, weighted error types
    "Bash": (0.11, {"exit_1": 48, "exit_2": 8, "permission_denied": 12, "hook_blocked": 12, "timeout": 9, "user_rejected": 5, "exit_127": 3}),
    "Edit": (0.06, {"edit_no_match": 60, "file_not_read_first": 25, "file_changed_since_read": 15}),
    "Write": (0.04, {"file_not_read_first": 1}),
    "Read": (0.02, {"file_not_found": 1}),
    "Grep": (0.01, {"input_validation": 1}),
    "WebFetch": (0.12, {"http_error": 70, "timeout": 30}),
    "WebSearch": (0.03, {"timeout": 1}),
    "mcp__tracker__get_issue": (0.08, {"tool_use_error": 1}),
    "mcp__docs__search": (0.05, {"tool_use_error": 1}),
    "shell": (0.10, {"exit_1": 55, "exit_2": 10, "exit_127": 5, "timeout": 15, "permission_denied": 15}),
    "apply_patch": (0.05, {"patch_failed": 1}),
    "mcp:tracker.search_issues": (0.06, {"mcp_error": 1}),
    "mcp:docs.lookup": (0.06, {"mcp_error": 1}),
}
CMDS = ["npm test", "npm run lint", "pnpm build", "pytest -q", "git status", "git diff", "git log", "make check",
        "tsc --noEmit", "docker compose up", "terraform plan", "ls", "rg pricing", "go test", "cargo test", "jq .items"]
FAIL_CMDS = ["npm test", "npm test", "pytest -q", "pytest -q", "pnpm build", "tsc --noEmit", "make check",
             "terraform plan", "docker compose up", "git push", "go test", "cargo test"]


def pick(rng, weights):
    keys = list(weights)
    return rng.choices(keys, [weights[k] for k in keys])[0]


def fake_id(rng):
    return "%08x-%04x-4%03x-%04x-%012x" % (rng.getrandbits(32), rng.getrandbits(16), rng.getrandbits(12),
                                         0x8000 | rng.getrandbits(14), rng.getrandbits(48))


def new_session(tool, sid, project, title, sub=False, parent=None):
    s = hs.new_session(tool, sid, sid + ".jsonl")
    s.update({"cwd": hs.HOME + "/development/" + project, "title": title, "subagent": sub, "parent": parent})
    return s


class Gen:
    """Builds analyzer-shaped session dicts (what parse_claude/parse_codex produce before finish_session)."""

    def __init__(self, rng):
        self.rng = rng
        self.sessions = []
        self.forced = []  # error types the next shell calls must hit (the showcase trace)
        self.used = {}  # parent id -> subagent briefs already used, so sibling lanes differ

    # ---- primitives
    def tokens(self, s, ctx, model, ts):
        r = self.rng
        tok = {"input": r.randint(40, 900), "output": int(min(r.lognormvariate(math.log(450), 0.8), 9000)),
               "cache_read": ctx["size"], "cache_write": r.randint(800, 6000) if r.random() < 0.5 else r.randint(100, 900)}
        ctx["size"] += tok["cache_write"] + tok["output"] // 2 + r.randint(200, 3000)
        if ctx["size"] > ctx["cap"]:  # context compaction resets the cached prefix
            ctx["size"] = r.randint(24000, 40000)
            s["compactions"] += 1
        hs.model_tokens(s, model, tok, ts)
        s["llm_calls"] = s.get("llm_calls", 0) + 1
        return sum(tok.values())

    def llm(self, s, ctx, model, t):
        """Claude Code generation span: from the previous logged event to the assistant message."""
        end = t + min(max(self.rng.lognormvariate(math.log(6), 0.7), 1.2), 75)
        s["generations"].append({"start": t, "end": end, "model": model, "tokens": self.tokens(s, ctx, model, end)})
        hs.touch(s, t)
        hs.touch(s, end)
        return end

    def duration(self, name, err):
        r = self.rng
        if err == "timeout":
            return r.choice([120.0, 120.0, 300.0, 600.0]) + r.random()
        med, sig = LAT[name]
        d = r.lognormvariate(math.log(med), sig)
        if name in ("Bash", "shell") and r.random() < 0.08:
            d = r.uniform(30, 240)  # a full test run or build
        if name in ("Bash", "Edit", "Write") and r.random() < 0.05:
            d += r.uniform(4, 55)  # waiting on a permission prompt is part of Claude Code latency
        return round(max(d, 0.005), 3)

    def call(self, s, name, t, model, err=None, target=None, ih=None, pending=False, head=None, dur=None):
        dur = self.duration(name, err) if dur is None else dur
        c = {"name": name, "start": t, "end": None if pending else t + dur, "ok": None if pending else err is None,
             "error_type": err, "input_hash": ih or hs.h([name, target, self.rng.random()]),
             "target": target or "path:" + hs.h(self.rng.random()), "model": model}
        if err and head:
            c["head"] = head
        if err == "user_rejected":
            s["interrupts"] += 1
        s["tool_calls"].append(c)
        hs.touch(s, t)
        if not pending:
            hs.touch(s, t + dur)
        return c

    def tool_step(self, s, name, t, model, shell_like):
        """One tool call, plus a retry when it fails. Returns the end time."""
        r = self.rng
        p, errs = ERR.get(name, (0, {}))
        err = pick(r, errs) if r.random() < p else None
        forced = bool(self.forced and name in shell_like and not s["subagent"])
        if forced:
            err = self.forced.pop(0)
        target, head = None, None
        if name in shell_like:
            cmd = r.choice(FAIL_CMDS if err else CMDS)
            target, head = "cmd:" + " ".join(cmd.split()[:2]), cmd.split()[0]
        c = self.call(s, name, t, model, err=err, target=target, head=head)
        end = c["end"]
        if err and err != "user_rejected" and (forced or r.random() < 0.65):
            exact = r.random() < 0.35
            again = err if r.random() < 0.25 and not forced else None
            t2 = end + r.uniform(1.5, 9)
            c2 = self.call(s, name, t2, model, err=again, target=c["target"], ih=c["input_hash"] if exact else None, head=head)
            end = c2["end"]
        return end

    # ---- subagents
    def claude_sub(self, parent, project, t, model):
        r = self.rng
        used = self.used.setdefault(parent["id"], set())
        desc, kind = r.choice([a for a in CLAUDE_AGENTS if a[0] not in used])
        used.add(desc)
        sid = "agent-a%016x" % r.getrandbits(64)
        s = new_session("claude-code", sid, project, desc, sub=True, parent=parent["id"])
        s["agent_type"], s["task"] = kind, desc + ". Report findings briefly."
        sm = "claude-sonnet-5-5" if r.random() < 0.7 else model
        ctx = {"size": r.randint(9000, 16000), "cap": 120000}
        t += r.uniform(0.4, 1.5)
        for _ in range(r.randint(4, 24)):
            t = self.llm(s, ctx, sm, t)
            n = 1 if r.random() < 0.6 else r.randint(2, 4)  # parallel reads
            ends = [self.tool_step(s, pick(r, CLAUDE_SUB_TOOLS), t + i * 0.04, sm, ("Bash",)) for i in range(n)]
            t = max(ends) + r.uniform(0.1, 0.8)
        t = self.llm(s, ctx, sm, t)
        self.sessions.append(s)
        return t

    def codex_sub(self, parent, project, t, model):
        r = self.rng
        s = new_session("codex", fake_id(r), project, None, sub=True, parent=parent["id"])
        used = self.used.setdefault(parent["id"], set())
        s["task"] = r.choice([a for a in CODEX_AGENTS if a not in used])
        used.add(s["task"])
        ctx = {"size": r.randint(9000, 16000), "cap": 120000}
        t += r.uniform(0.5, 2)
        s["turns"].append({"start": t, "end": None, "id": "turn-1"})
        hs.touch(s, t)
        for _ in range(r.randint(4, 18)):
            t += r.uniform(2, 14)
            self.tokens(s, ctx, model, t)
            hs.touch(s, t)
            t = self.tool_step(s, pick(r, CODEX_SUB_TOOLS), t, model, ("shell",)) + r.uniform(0.2, 1)
        t += r.uniform(2, 8)
        self.tokens(s, ctx, model, t)
        hs.touch(s, t)
        s["turns"][0]["end"] = t
        self.sessions.append(s)
        return t

    # ---- main sessions
    def main_session(self, idx, project, title, tool, start, n_turns, spawn_turns, max_steps=12):
        r = self.rng
        claude = tool == "claude-code"
        sid = fake_id(r)
        s = new_session(tool, sid, project, title)
        if claude:
            model = "claude-opus-5-5" if r.random() < 0.75 else "claude-sonnet-5-5"
        else:
            model = "gpt-6-astra" if r.random() < 0.65 else "gpt-6.1-sol"
        ctx = {"size": r.randint(18000, 28000), "cap": 175000}
        tools = CLAUDE_TOOLS if claude else CODEX_TOOLS
        shell_like = ("Bash",) if claude else ("shell",)
        t = start
        limit = UNTIL - 3 * 3600
        for ti in range(n_turns):
            if ti and t > limit:
                break
            if ti == 0:
                text = title.lower() + r.choice(OPENERS)
            elif r.random() < 0.04:
                text = r.choice(SLASH)
            else:
                text = r.choice(FOLLOW)
            s["prompts"].append({"ts": t, "type": hs.classify(text), "snippet": hs.snippet(text), "slash": text.startswith("/")})
            hs.touch(s, t)
            tm = model if r.random() > 0.08 else (CLAUDE_MODELS if claude else CODEX_MODELS)[1 - (CLAUDE_MODELS if claude else CODEX_MODELS).index(model)]
            turn = {"start": t, "end": None, "id": "turn-%d" % (ti + 1)}
            aborted = (not claude) and r.random() < 0.07
            steps = r.randint(2, max_steps) if ti < n_turns - 1 or n_turns == 1 else r.randint(2, min(6, max_steps))
            if aborted:
                steps = r.randint(1, 3)
            for step in range(steps):
                if claude:
                    t = self.llm(s, ctx, tm, t)
                else:
                    t += r.uniform(2, 16)
                    self.tokens(s, ctx, tm, t)
                    hs.touch(s, t)
                if step == 0 and ti in spawn_turns:  # fan out subagents
                    fan = spawn_turns[ti]
                    ends = []
                    for k in range(fan):
                        ts = t + k * 0.06
                        if claude:
                            end = self.claude_sub(s, project, ts, tm) + r.uniform(0.3, 1.2)
                            self.call(s, "Agent", ts, tm, target="agent:" + hs.h(r.random()), dur=round(end - ts, 3))
                        else:
                            self.call(s, "collaboration.spawn_agent", ts, tm, dur=round(r.uniform(0.2, 0.6), 3))
                            end = self.codex_sub(s, project, ts, tm) + r.uniform(0.3, 1.2)
                        ends.append(end)
                    if not claude:
                        self.call(s, "collaboration.wait", t + 0.8, tm, dur=round(max(ends) - t - 0.8, 3))
                    t = max(ends) + r.uniform(0.3, 1.5)
                    continue
                if claude and step > 0 and r.random() < 0.1:
                    continue  # text-only reply
                n = 1 if r.random() < 0.72 else r.randint(2, 3)
                ends = []
                for i in range(n):
                    name = pick(r, tools)
                    if not claude and name == "shell" and r.random() < 0.15:  # exec script wrapper around a shell call
                        w = {"name": "exec", "start": t, "end": t + 0.5, "ok": r.random() > 0.05, "error_type": None,
                             "input_hash": hs.h(r.random()), "target": None, "model": tm}
                        s.setdefault("exec_wrappers", []).append(w)
                    ends.append(self.tool_step(s, name, t + i * 0.05, tm, shell_like))
                t = max(ends) + r.uniform(0.2, 1.5)
            if claude:
                t = self.llm(s, ctx, tm, t)  # the answer
            else:
                t += r.uniform(2, 10)
                self.tokens(s, ctx, tm, t)
                hs.touch(s, t)
            turn["end"] = t
            if aborted:
                turn["aborted"] = True
                s["interrupts"] += 1
            if not claude:
                s["turns"].append(turn)
            if claude and r.random() < 0.05:
                s["interrupts"] += 1  # "[Request interrupted by user]"
            last_end = t
            gap = r.random()
            t += r.uniform(15, 240) if gap < 0.7 else r.uniform(240, 1200) if gap < 0.92 else r.uniform(2100, 5400)
        if idx % 13 == 5:  # a few sessions end with a call that never got a result
            self.call(s, "Bash" if claude else "shell", last_end + r.uniform(1, 4), model, target="cmd:npm run", pending=True)
            s["interrupts"] += 1
        self.sessions.append(s)
        return s


def plan(rng):
    """Day, hour, turns and subagent fan-out per main session, trimmed to SUB_RUNS subagent runs in total."""
    day_w = [0.25, 1.0, 1.1, 1.2, 0.9, 0.45, 0.4, 0.9]  # Mon 19 Oct evening, then Tue 20 .. Mon 26 Oct
    plans = []
    for idx, (_, _, tool) in enumerate(SESSIONS):
        claude = tool == "claude-code"
        if idx == 0:  # the showcase trace: errors, retries and subagent lanes, few enough turns to stay unfolded
            plans.append({"day": 2, "hour": 10.25, "turns": 8, "spawns": {0: 2, 3: 1, 5: 1}, "max_steps": 5, "fixed": True})
            continue
        day = rng.choices(range(-1, 7), day_w)[0]
        hour = rng.uniform(20.3, 22.5) if day < 0 else rng.uniform(8.5, 13.5 if day == 6 else 21.5)
        turns = rng.choice([1, 2, 3, 4, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 14, 16, 19, 22])
        spawns = {}
        for _ in range(rng.choice([0, 0, 1, 1, 1, 1, 2, 3] if claude else [0, 0, 1, 1, 2])):
            spawns[rng.randrange(turns)] = rng.choice([1, 1, 1, 2, 3] if claude else [1, 1, 2])
        plans.append({"day": day, "hour": hour, "turns": turns, "spawns": spawns, "max_steps": 12})
    while sum(n for p in plans for n in p["spawns"].values()) > SUB_RUNS:
        p = rng.choice([p for p in plans if p["spawns"] and not p.get("fixed")])
        k = rng.choice(sorted(p["spawns"]))
        p["spawns"][k] -= 1
        if not p["spawns"][k]:
            del p["spawns"][k]
    return plans


def build(seed):
    g = Gen(random.Random(seed))
    for idx, ((project, title, tool), p) in enumerate(zip(SESSIONS, plan(random.Random(seed + 1)))):
        g.forced = ["exit_1", "hook_blocked", "timeout"] if idx == 0 else []
        g.main_session(idx, project, title, tool, DAY0 + p["day"] * 86400 + p["hour"] * 3600, p["turns"], p["spawns"], p["max_steps"])
    return g.sessions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "sample-summary.json"))
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    raw = build(a.seed)
    sessions = [x for x in (hs.finish_session(s) for s in raw) if x]
    codex_prompts = sum(len(s["prompts"]) for s in sessions if s["tool"] == "codex" and not s["subagent"])
    out = hs.summarise(sessions, SINCE, UNTIL, codex_prompts, [], 200)
    out["timezone"] = "UTC"
    out["sample"] = True
    out["notes"] = dict([("sample", "Synthetic demo data from examples/make_sample.py (fixed seed). "
                                    "No real sessions, people, projects, prompts or paths.")] + list(out["notes"].items()))
    with open(a.out, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
        fh.write("\n")
    hd = out["headline"]
    print("sample: sessions %d (+%d subagent runs), prompts %d, tool calls %d, error rate %s, tokens %d, p95 %ss -> %s (%.2f MB)" % (
        hd["sessions"], hd["subagent_runs"], hd["user_prompts"], hd["tool_calls"], hd["error_rate"], hd["tokens"],
        hd["p95_tool_latency_s"], os.path.relpath(a.out, os.path.join(HERE, "..")), os.path.getsize(a.out) / 1e6))


if __name__ == "__main__":
    main()
