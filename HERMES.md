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
- 与组合入口和质量技能共存时，使用同一任务编排：APP UI Studio 持有当前范围与证据，其他技能只交当前分派阶段；不重复定方向、审计或自动卸载。缺少外部技能时可用本插件已有规范与 `studio.py web-report --baseline`。
