---
name: codex-context-window
description: Preview and safely update Codex user configuration and model-catalog context windows. Use when listing configured models, resolving aliases such as sol, terra, luna, or all-gpt-5.6, changing context_window, max_context_window, effective_context_window_percent, model_context_window, or the automatic history-compaction token limit.
---

# Codex Context Window

Run `scripts/manage_context_window.py` against the active Codex configuration,
which defaults to `~/.codex/config.toml`.

## Workflow

1. List the catalog with `--list` or inspect the default preview. Accept model
   slugs, `sol`, `terra`, `luna`, and `all-gpt-5.6`.
2. Preview before applying. The script resolves the selected models and prints
   `usable_context_tokens = context_window * effective_context_window_percent / 100`
   without modifying any files.
3. Apply only after reviewing the preview. `--apply` creates timestamped backups
   of both `config.toml` and the catalog before updating them.

```bash
python3 scripts/manage_context_window.py \
  --models all-gpt-5.6 --context-window 1m --effective-percent 95

python3 scripts/manage_context_window.py \
  --models all-gpt-5.6 --context-window 1m --effective-percent 95 --apply
```

`--effective-percent` controls the usable portion of a model's context window.
`--history-compaction-limit` is independent: omit it to preserve each model's
existing `truncation_policy.limit`, or provide it explicitly to update that
automatic history-compaction threshold.

Validate an applied configuration with `codex --strict-config exec --help`.
