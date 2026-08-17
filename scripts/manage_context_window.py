#!/usr/bin/env python3
"""Preview and apply model context-window changes without ambiguous side effects."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path


ALIASES = {"sol": "gpt-5.6-sol", "terra": "gpt-5.6-terra", "luna": "gpt-5.6-luna"}
DEFAULT_CATALOG = Path.home() / ".codex" / "model-catalogs" / "rlab.json"


def parse_tokens(value: str) -> int:
    match = re.fullmatch(r"([1-9][0-9]*)([kKmM]?)", value.strip())
    if not match:
        raise argparse.ArgumentTypeError("use a positive integer, optionally ending in k or m")
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).lower()]
    return int(match.group(1)) * multiplier


def read_config(path: Path) -> dict:
    """Read only top-level string values needed by this dependency-free script."""
    lines = path.read_text(encoding="utf-8").splitlines()
    table_started = False
    result: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            table_started = True
        if table_started:
            continue
        match = re.match(r'^([A-Za-z0-9_-]+)\s*=\s*"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$', stripped)
        if match:
            result[match.group(1)] = json.loads(f'"{match.group(2)}"')
    return result


def resolve_catalog(config: dict, explicit_catalog: str | None) -> Path:
    if explicit_catalog:
        return Path(explicit_catalog).expanduser().resolve()
    configured = config.get("model_catalog_json")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_CATALOG.resolve()


def select_models(models: list[dict], requested: list[str]) -> list[dict]:
    by_slug = {model.get("slug"): model for model in models if model.get("slug")}
    selected: list[dict] = []
    for token in requested:
        normalized = token.strip().lower()
        if normalized == "all-gpt-5.6":
            matches = [model for model in models if str(model.get("slug", "")).startswith("gpt-5.6-")]
        else:
            slug = ALIASES.get(normalized, token)
            matches = [by_slug[slug]] if slug in by_slug else []
        if not matches:
            raise ValueError(f"unknown model or alias: {token}")
        for model in matches:
            if model not in selected:
                selected.append(model)
    return selected


def upsert_top_level_key(text: str, key: str, rendered_value: str) -> str:
    lines = text.splitlines(keepends=True)
    table_start = next((index for index, line in enumerate(lines) if line.lstrip().startswith("[")), len(lines))
    assignment = re.compile(rf"^(\s*){re.escape(key)}\s*=.*(?:\n|$)")
    for index in range(table_start):
        match = assignment.match(lines[index])
        if match:
            lines[index] = f"{match.group(1)}{key} = {rendered_value}\n"
            return "".join(lines)
    lines.insert(table_start, f"{key} = {rendered_value}\n")
    return "".join(lines)


def backup(path: Path, suffix: str) -> Path:
    target = path.with_name(f"{path.name}.bak.{suffix}")
    shutil.copy2(path, target)
    return target


def describe(model: dict, context_window: int, effective_percent: int, compaction: int | None) -> str:
    usable = context_window * effective_percent // 100
    compact_text = "unchanged" if compaction is None else str(compaction)
    return (
        f"{model['slug']}: context_window={context_window:,}, "
        f"max_context_window={context_window:,}, effective_context_window_percent={effective_percent}, "
        f"usable_context_tokens={usable:,}, history_compaction_limit={compact_text}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path.home() / ".codex" / "config.toml"))
    parser.add_argument("--catalog", help="Override the model catalog path.")
    parser.add_argument("--list", action="store_true", help="List catalog models and exit.")
    parser.add_argument("--models", nargs="+", default=["all-gpt-5.6"])
    parser.add_argument("--context-window", type=parse_tokens, default=parse_tokens("1m"))
    parser.add_argument("--effective-percent", type=int, default=95)
    parser.add_argument("--history-compaction-limit", type=parse_tokens)
    parser.add_argument("--apply", action="store_true", help="Write changes after previewing the calculation.")
    args = parser.parse_args()
    if not 1 <= args.effective_percent <= 100:
        parser.error("--effective-percent must be between 1 and 100")

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.is_file():
        parser.error(f"active config not found: {config_path}")
    config = read_config(config_path)
    catalog_path = resolve_catalog(config, args.catalog)
    if not catalog_path.is_file():
        parser.error(f"model catalog not found: {catalog_path}")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    models = catalog.get("models")
    if not isinstance(models, list):
        parser.error("catalog must contain a models array")
    if args.list:
        for model in models:
            print(f"{model.get('slug', '<missing>')}: {model.get('display_name', model.get('displayName', ''))}")
        return 0
    try:
        selected = select_models(models, args.models)
    except ValueError as error:
        parser.error(str(error))

    print(f"Active config: {config_path}")
    print(f"Model catalog: {catalog_path}")
    print("Preview (no files have been written):")
    for model in selected:
        print("  " + describe(model, args.context_window, args.effective_percent, args.history_compaction_limit))
    print(f"  model_context_window={args.context_window:,}")
    if not args.apply:
        print("Run again with --apply to create backups and write these changes.")
        return 0

    for model in selected:
        model["context_window"] = args.context_window
        model["max_context_window"] = args.context_window
        model["effective_context_window_percent"] = args.effective_percent
        if args.history_compaction_limit is not None:
            policy = model.setdefault("truncation_policy", {"mode": "tokens"})
            policy["mode"] = "tokens"
            policy["limit"] = args.history_compaction_limit

    timestamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    config_backup = backup(config_path, timestamp)
    catalog_backup = backup(catalog_path, timestamp)
    config_text = config_path.read_text(encoding="utf-8")
    config_text = upsert_top_level_key(config_text, "model_context_window", str(args.context_window))
    config_text = upsert_top_level_key(config_text, "model_catalog_json", json.dumps(str(catalog_path)))
    config_path.write_text(config_text, encoding="utf-8")
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    # The active Codex binary is the authoritative TOML parser; callers can run
    # `codex --strict-config exec --help` to validate unsupported or malformed keys.
    read_config(config_path)
    json.loads(catalog_path.read_text(encoding="utf-8"))
    print(f"Applied. Backups: {config_backup}, {catalog_backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
