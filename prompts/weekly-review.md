# Prompt: weekly harness review

Use with the `harness-observatory` skill installed.

```text
Run the harness-observatory skill for the last 7 days in ~/harness-reports/<this week's date>.
Render the dashboard, then write HARNESS.md comparing against last week's HARNESS.md in
~/harness-reports if one exists: what improved, what got worse, and which earlier proposals the new data
supports or contradicts. Show me the 5 headline numbers and the proposed diff. Change no config.
```

Shorter variants:

- `Refresh my harness dashboard.` (steps 1 to 4 only)
- `Which of my sessions burned the most tokens this week, and why?` (Budget section only)
- `What are my top 3 agent failure patterns this week?` (Guardrails section only)
