# Codex Context Window

[简体中文](README.zh-CN.md)

A dependency-free Codex skill for inspecting and safely adjusting model context-window settings in a local Rlab-compatible model catalog.

It resolves common aliases (`sol`, `terra`, `luna`, and `all-gpt-5.6`), calculates usable context before it writes, and keeps the context-window percentage separate from the automatic history-compaction token limit.

## What it changes

When explicitly applied, the bundled script updates:

- Selected catalog entries: `context_window`, `max_context_window`, and `effective_context_window_percent`.
- The active user configuration: `model_context_window` and `model_catalog_json`.

It never writes during preview. An applied run creates timestamped backups of both affected files before making a change.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/seanbabalala/codex-context-window.git ~/.codex/skills/codex-context-window
```

The script uses only the Python 3.9+ standard library.

## Quick start

List available models:

```bash
python3 scripts/manage_context_window.py --list
```

Preview a 1M context window for every GPT-5.6 catalog entry:

```bash
python3 scripts/manage_context_window.py \
  --models all-gpt-5.6 \
  --context-window 1m \
  --effective-percent 95
```

The preview reports 950,000 usable tokens for this example and changes no files. Apply the reviewed result with:

```bash
python3 scripts/manage_context_window.py \
  --models all-gpt-5.6 \
  --context-window 1m \
  --effective-percent 95 \
  --apply
```

## Why a 1M context window matters

A larger context window lets an agent retain substantially more of the working set for a complex task. With a 1,000,000-token window (950,000 usable tokens at 95%), Codex can more often keep the relevant repository structure, architecture decisions, specifications, logs, and prior investigation in one coherent thread.

This is especially valuable for:

- **Large repositories:** trace behavior across services, shared libraries, migrations, tests, and deployment configuration without repeatedly discarding earlier findings.
- **Long-running debugging:** preserve stack traces, reproduction notes, failed hypotheses, and incremental fixes so investigation does not restart from a compressed summary.
- **Cross-cutting changes:** reason about a feature that spans frontend, backend, data models, APIs, infrastructure, and documentation at the same time.
- **Document-heavy work:** compare lengthy requirements, design notes, incident reports, and generated artifacts alongside implementation details.
- **Fewer context handoffs:** reduce repeated file discovery, re-explanations, and summary-induced loss of detail, which can improve continuity and make reviews more consistent.

A larger configured window is capacity, not a guarantee of better answers. Response quality, cost, latency, and the actual accepted context length remain dependent on the selected model and its upstream provider.

## Safety and validation

- The active configuration defaults to `~/.codex/config.toml`.
- The catalog is taken from `model_catalog_json` when configured, otherwise `~/.codex/model-catalogs/rlab.json`.
- `--history-compaction-limit` is optional and independent of `--effective-percent`; omit it to preserve the existing compaction limit.
- Validate the applied configuration with `codex --strict-config exec --help`.

The catalog controls what Codex advertises locally; the upstream model provider must independently support the requested context window.
