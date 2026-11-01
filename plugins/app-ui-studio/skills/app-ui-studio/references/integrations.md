# 四技能协作与可选依赖

它们是外部、可选的本地增强，未复制入插件；原技能保留原名、原文件和完整职责。宿主没有文件系统时采用本插件基础流程，并明确增强不可访问。

优先使用宿主当前暴露的技能路径。无清单时可用 `studio.py doctor` 按 `$CODEX_HOME/skills`（若设置）、`~/.codex/skills`、`~/.agents/skills` 检测；同名冲突由宿主已选择的版本优先，不静默合并。结果仅表示入口/脚本存在，不等于 host enabled、引擎运行或项目验收。把实际 base path 代入命令，不能把下面的占位路径直接执行。

| 调用 | 适用职责 | 关键边界 |
|---|---|---|
| `$ui-ux-pro-max` | 产品设计系统、结构、颜色、字阶、图表与 UX/技术栈检索 | 新页面可生成 design-system；窄问题用 domain；结果需核对产品与平台，空命中按原技能降级 |
| `$mobile-app-design` | 原生平台习惯、触控、字体缩放、读屏、移动性能和设备测试 | 原生 pt/dp 不等于 CSS px；静态扫描不证明真实热区 |
| `$design-taste-frontend`（Taste Skill） | 完整艺术指导、构图、布局、密度、视觉表达、实现与看图修复 | 读取实际安装版本；有 APP 专用规则时使用，不能缩减为上色或只用于营销页 |
| `$impeccable audit` / `$impeccable polish` | 技术/UX审查与最终精修，也覆盖布局、文案、动效和状态 | 按原生/网页 playbook；context 不能运行时按其降级规则；不顺带修复 drift 或启用 hooks |

冲突处理顺序：用户明确要求与项目事实 → 原生平台行为/无障碍约束 → 项目既有设计系统 → 本次选定设计方向 → 通用库建议。Taste 的营销页 house rules 不覆盖 APP 的导航、合法分隔线和重复列表。品牌和参考图明确要求的风格可保留，冲突具体记录，不以通用反模板偏好静默删除。设计系统落点保留项目现有规范：MASTER、DESIGN、direction sheet 作为不同视角互相映射，不创建第二套互斥 tokens。

## 版本与系统兼容

以宿主可见的 `SKILL.md` 和实际文件为准，不把上游最新版接口强加给已安装版本。2026-11-02 本机核对：Taste 安装仅提供 `SKILL.md`，没有 `references/app-screens.md`、`scripts/draw.mjs` 或 `scripts/inspect.mjs`。这是资源缺失，不能报告已运行。保留现有 Taste；直接应用可读的规则，APP 行为结合 Mobile 规范，截图使用宿主浏览器。未来版本出现对应文件后再按该版本说明加载，不能自动安装/替换以消除差异。

## 命令参考

先读实际版本的 SKILL.md 与 --help；以下是 macOS/Linux 的参数化参考，需先替换实际目录、产品与栈，不保证上游以后不变：

```bash
python3 "<pro-max-base>/scripts/search.py" "focus timer mobile" --design-system -p "Product"
python3 "<pro-max-base>/scripts/search.py" "keyboard focus modal" --domain ux -n 2
python3 "<pro-max-base>/scripts/search.py" "safe area navigation" --stack "<项目实际技术栈>"
python3 "<mobile-base>/scripts/check-contrast.py" "#202020" "#FAFAFA"
"<impeccable-base>/scripts/impeccable" context
```

Windows 用可用的 Python 3（例如 `py -3.11`）；PowerShell 调 Impeccable 时使用 `& "<impeccable-base>/scripts/impeccable.cmd" context`。不用 `.cmd` 作为 macOS 入口。以上命令只在任务需要该能力时运行，不因能力盘点启动引擎。

Taste 的营销页规则不能直接覆盖 APP 操作界面；按当前版本中适用的完整规则处理并保留平台约束。原生 UI 不能宣称浏览器验收了原生渲染。UI/UX Pro Max 持久化需显式 `--output-dir <项目根>`，不擅自加 `--force` 覆盖。Mobile 的 `.sh` 检查依赖 Bash 且只是启发式，不作为唯一依据。

Impeccable context 每个会话按原技能执行一次，可能首次下载固定版本引擎；先核对当前环境与任务约束。用户要求本地且禁止下载时不触发下载。launcher 拒绝/失败时先告知 context 未运行，再直接读取现有 PRODUCT.md、DESIGN.md 与所需 playbook；不编造缺失文件。CONTEXT_STALE 默认报告，不自动 doctor、repair drift、pin 或 hooks；原技能明确标记 auto 的随写入行为按其规则处理。

缺依赖时：不伪称调用成功，不为此反复安装；继续能做的阶段。无 Node/浏览器时采用可用截图与人工复核并标 inspector 未执行；无图像工具交付 prompts；无设计工具交付 tokens/素材/组件映射与导入说明，将真实编辑器转换留为 not_executed。
