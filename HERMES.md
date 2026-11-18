# Hermes 宿主安装说明

技能本体与 Codex 相同（`plugins/app-ui-studio/skills/app-ui-studio`），Hermes 侧只需复制目录。

## 安装

```bash
mkdir -p ~/.hermes/skills/creative
cp -R plugins/app-ui-studio/skills/app-ui-studio ~/.hermes/skills/creative/app-ui-studio
```

## 验证

```bash
python3 ~/.hermes/skills/creative/app-ui-studio/scripts/studio.py --help
python3 ~/.hermes/skills/creative/app-ui-studio/scripts/studio.py doctor --project "<项目目录>"
```

`studio.py` 只用 Python 标准库，macOS 自带 Python 3.9 即可运行（已在 3.9.6 上验证）。

## Hermes 侧差异

- 无 CORDIS/hook/`/hooks` 审核流程；技能靠自身流程约束执行。
- 无内置 MCP 服务器，也不需要。
- 桌面端展示本地 HTML 产物用 `::preview{file="<绝对路径>"}`。
- 与 `ui-design-quality-toolkit` 功能重叠：本技能已含设计规范、Modern Web 质量检查与
  Lighthouse 报告对比（`studio.py web-report --baseline`），不需要在同一宿主里重复安装。
