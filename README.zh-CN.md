# Codex 上下文窗口管理

[English](README.md)

这是一个零第三方依赖的 Codex Skill，用于查看并安全调整本地 Rlab 兼容模型目录中的上下文窗口配置。

它支持常用别名（`sol`、`terra`、`luna` 和 `all-gpt-5.6`），会在写入前计算实际可用上下文，并将有效上下文比例与自动历史压缩 token 阈值分别管理。

## 会修改什么

仅当显式传入 `--apply` 时，脚本才会更新：

- 所选模型条目的 `context_window`、`max_context_window` 和 `effective_context_window_percent`；
- 当前用户配置中的 `model_context_window` 和 `model_catalog_json`。

预览模式不会写入任何文件。应用变更时，脚本会先为两份受影响的文件创建带时间戳的备份。

## 安装

将仓库克隆到 Codex skills 目录：

```bash
git clone https://github.com/seanbabalala/codex-context-window.git ~/.codex/skills/codex-context-window
```

脚本只使用 Python 3.9+ 标准库。

## 快速开始

列出可用模型：

```bash
python3 scripts/manage_context_window.py --list
```

预览将所有 GPT-5.6 模型设为 1M 上下文窗口：

```bash
python3 scripts/manage_context_window.py \
  --models all-gpt-5.6 \
  --context-window 1m \
  --effective-percent 95
```

以上命令只会预览，不会修改文件。在该示例中，1,000,000 token 的总窗口在 95% 有效比例下可用上下文为 950,000 token。确认预览结果后，执行：

```bash
python3 scripts/manage_context_window.py \
  --models all-gpt-5.6 \
  --context-window 1m \
  --effective-percent 95 \
  --apply
```

## 为什么 1M 上下文窗口很重要

更大的上下文窗口，意味着智能体在处理复杂任务时能够同时保留更多关键工作信息。以 1,000,000 token 的总窗口为例，在 95% 有效比例下可使用约 950,000 token；Codex 因而更有机会在同一个连贯的工作线程中持续理解代码仓库结构、架构决策、需求文档、运行日志以及先前的排查结论。

这对以下场景尤为有价值：

- **大型代码库：** 可以同时追踪服务、共享库、数据库迁移、测试和部署配置之间的关系，减少因早期信息被挤出上下文而反复重新定位问题的情况。
- **长链路调试：** 能持续保留堆栈信息、复现步骤、已验证或排除的假设，以及逐步形成的修复方案，避免每次都从压缩后的摘要重新开始推理。
- **跨领域改动：** 当一个功能同时涉及前端、后端、数据模型、API、基础设施与文档时，能够在更完整的全局视角下评估影响范围和实现路径。
- **文档密集型工作：** 可以将较长的需求说明、设计文档、事故报告和生成产物与具体实现放在同一上下文中比对和推敲。
- **减少上下文交接：** 降低重复搜索文件、反复补充背景与摘要压缩导致细节丢失的频率，让任务推进和代码审查更连贯、更稳定。

更大的配置窗口代表更高的上下文容量，并不自动保证更高质量的回答。实际效果、响应延迟、成本以及最终可接受的上下文长度，仍取决于所选模型及其上游服务商。

## 安全与验证

- 默认读取当前生效的配置文件：`~/.codex/config.toml`。
- 若配置中存在 `model_catalog_json`，则使用该目录；否则使用 `~/.codex/model-catalogs/rlab.json`。
- `--history-compaction-limit` 与 `--effective-percent` 相互独立；不传前者即可保留当前自动历史压缩阈值。
- 应用后，可运行 `codex --strict-config exec --help` 验证配置。

模型目录控制的是 Codex 在本地声明的能力；上游模型服务商仍需实际支持所请求的上下文窗口。
