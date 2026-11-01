# APP UI Studio 2.1.0

统一入口：`$app-ui-studio`。这是技能与本地辅助工具组成的私有插件，支持多屏 APP 和宣传页设计；通过宿主实际提供的 Lovart / image 生成图像。不附带模型服务或 Figma 转换服务器。

2.0 新增可组合提示词库：**20类软件功能 × 16行业 × 新建/已有/混合 × 产品/宣传页 × 三档视觉**。先按功能选择类型，再叠加行业约束；这是覆盖清单，不是流行度排名。只有命中的配置按需加载，不新增36个技能入口。

```text
$app-ui-studio 为制造业项目新增AI协作工作台和宣传页
software=ai-agent industry=manufacturing scope=mixed surface=both tone=tech-refined
```

```text
python3 "<技能目录>/scripts/studio.py" catalog --kind all
python3 "<技能目录>/scripts/studio.py" prompt --software ai-agent --industry manufacturing --scope existing --surface both --tone tech-refined
python3 "<技能目录>/scripts/studio.py" export-prompts --output "<不存在的新目录>"
```

导出包含20份软件提示词、16份行业提示词及说明/清单；组合器无外部依赖，不调用模型或读取项目。实际制作时智能体还需读取项目、实际加载四技能并执行工具、渲染与交互检查。Windows将 `python3` 替换为已核验的 `py -3.11` 等Python 3入口。完整机制见 `skills/app-ui-studio/references/prompt-library.md`。

可选 SaaS 模式：

```text
$app-ui-studio saas
scope=existing
surface=both
tone=tech-expressive
项目目录：<实际项目目录>
目标：为现有 AI SaaS 打磨界面和宣传页，保持已确认的导航、品牌及业务契约。
视觉：专业、精密、科技、精致、友好；工作台使用语义状态流与细致反馈，宣传页加强品牌光场及局部 3D。
素材：按既有授权让 Lovart 与图像工具分别产出，并接入真实组件后验证。
```

`scope` 支持 auto/new/existing/mixed；`surface` 支持 product/marketing/both；`tone` 支持 calm、tech-refined（SaaS 默认）和 tech-expressive。选择 SaaS 才应用这套模式，普通 APP 流程保持原行为。完整可复制模板见 `skills/app-ui-studio/assets/saas-prompt.md`。

本地配置与交接工具（使用当前电脑实际 Python 3）：

```text
python3 "<技能目录>/scripts/studio.py" preset saas --scope existing --surface both --tone tech-expressive
python3 "<技能目录>/scripts/studio.py" init --mode saas --output "<不存在的新目录>"
python3 "<技能目录>/scripts/studio.py" check "<项目根>/delivery.json"
```

`preset` 只输出草案；`init` 不覆盖已有目录；`check` 只校验文件契约。它们不会调用 Lovart 或图像服务。真实生成由智能体使用当前宿主的实际工具与授权执行；无工具、额度或必要授权时留下准确未执行状态。两工具的执行与实际 UI 质量不能由本地脚本代为证明。

原有通用入口：

```text
$app-ui-studio
为「我的产品」制作 APP 界面。
用户与任务：……
平台：iOS / Android / 跨平台原生 / 移动 Web。
页面：……
品牌与参考素材：……（文件或链接）
项目目录与技术栈：……；没有项目时先做本地 HTML 交互原型。
交付：品牌与设计 tokens、多屏界面、可运行代码、截图比对和验证报告。
如果需要 Figma：先完成本地交接包，再按实际可用工具完成转换并验证独立图层。
```

只生成提示词时加 `prompts`；宣传页加 `marketing`；仅检查加 `audit`；精修加 `polish`；代码还原加 `reconstruct`；设计交接加 `handoff`。这些是技能内路由参数，不是新 MCP 工具。

```text
$app-ui-studio marketing
为现有 APP 制作宣传落地页，复用项目品牌、IP 和真实界面截图。
根据实际工具，用 Lovart 或 image 辅助主视觉；页面保留可编辑文本与真实按钮。
交付可运行源码、手机与桌面截图和关键行动验证；不自动上线。
```

1.1.0 补齐宣传页流程、媒体工具适配与原创提示词；修正 macOS 命令示例和旧版 Taste 缺少脚本/参考文件时的降级。升级沿用现有插件身份，保留原有四项技能。

本地增强技能从宿主技能目录读取，不打包、不替换、不重命名原技能：`ui-ux-pro-max`、`mobile-app-design`、`design-taste-frontend`、`impeccable`。缺少时使用本插件的基础流程并明确哪些增强未执行。

本插件包含：工作流、原创提示词模板、项目交接模板、只读依赖检测、安全初始化和 WCAG 对比度计算。图像、浏览器、设计工具、原生设备验证依赖宿主实际能力；插件创建和文件校验不代表真实 APP 或可编辑 Figma 已验收。

来源与改编边界见技能内 `references/article-method.md`。现有技能的许可证与更新仍由各自上游管理；本包未复制其源代码或知识库。

## 2.1 合并与证据比较

保留2.0软件/行业提示词库、catalog/prompt/export-prompts和既有设计流程，合并1.3版本冻结、同状态捕获、媒体阶段区分和compare命令。比较文件契约不证明视觉质量，详细规则见 `skills/app-ui-studio/references/comparison.md`。
