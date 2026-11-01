---
name: app-ui-studio
description: "APP / SaaS 界面与宣传页设计、实现和精修，含可选科技视觉模式。适配新建与已有项目，协作四项设计技能及宿主 Lovart / image，交付实际组件、素材与验证证据。"
---

# APP UI Studio

把品牌、用户任务、结构和素材贯穿到实际界面。默认简体中文。用户只要分析时交付分析；要求制作时持续到所需产物与适当验证完成。

## 入口与能力发现

支持自然语言，或 `brief`、`prompts`、`design`、`saas`、`marketing`、`reconstruct`、`audit`、`polish`、`handoff` 参数。这些是技能路由，不是 MCP 工具或独立命令。无参数时从用户目标继续，只在实质缺口阻碍结果时提问。没有新建项目指令时不因调用插件就生成模板。

`saas` 是可选设计模式。用户选择 SaaS，或任务明确为 SaaS 产品时，读取 [saas-mode.md](references/saas-mode.md)，复用下述工作流。`scope=auto/new/existing/mixed` 决定如何处理项目现状，`surface=product/marketing/both` 决定交付面；未指定时先读项目推断。`tone=calm/tech-refined/tech-expressive` 控制视觉表达，SaaS 默认 `tech-refined`，其他模式保持原行为。科技风格遵从用户 brief，不把通用去装饰偏好当成对玻璃、光场或局部 3D 的绝对禁令；例外限定表面，仍检查可读性、交互和动效降级。

非 SaaS 项目指定“科技、酷炫、AI 智能体视觉”或 tech tone 时，可读取 [tech-visual-language.md](references/tech-visual-language.md) 作为视觉修饰，不改变业务模式、品牌或项目技术栈。

1. 确认目标目录、适用项目规范、工作树与现有 UI。区分原生 APP、移动 Web、桌面工作界面、营销页面；手机宽度不等于原生 APP。
2. 使用宿主暴露的技能清单解析技能目录；有本地执行能力时可运行 `python3 "<本技能目录>/scripts/studio.py" doctor --project "<项目目录>"`。按当前环境选择已安装的 Python 3；Windows 可用 `py -3` 或经核验的 `python`。doctor 仅检测文件与运行时，不证明技能已启用或引擎已运行。
3. 需要四技能增强时读 [integrations.md](references/integrations.md)，只加载当前阶段所需的实际 `SKILL.md`。不覆盖现有安装、不自动安装依赖、不改 hook。缺技能仍能按下述基础流程工作，并写明增强未执行。
4. 图像和设计工具以当前工具列表为准。需要 Lovart 或 image 时读 [media-tools.md](references/media-tools.md)，遵循宿主工具规范和现有授权。用户要求两者参与时，为两者分别分配实际产物，不能只调用一个就称已完成双方协作。按“素材计划 → 真实生成/编辑 → 查看并筛选 → 项目落地 → 组件接入 → 渲染验证”留证。缺能力时交付可用提示词并记录未执行阶段，不因安装本插件就生成图或产生付费任务。
5. `marketing` / 宣传页 / 落地页 / 海报请求读 [marketing.md](references/marketing.md)。APP 与宣传页同做时复用品牌和已完成屏幕；宣传图不能代替真实 APP 屏幕。仅宣传页任务不强制先制作完整 APP。

## 按目标选择阶段

完整新设计按以下依赖推进；已有品牌、代码或参考图时从对应阶段切入，复用既有产物。提示词任务完成于可用 prompts；审查任务不修改代码。不要为了凑阶段重做已有设计。

### 1. 品牌与任务

记录产品、用户、主要任务、目标平台、页面、品牌、参考素材及交付格式。优先读项目现有需求与设计系统；不要创建相互竞争的事实源。缺省且易回退的事项标为假设继续。

品牌定义保留 logo、吉祥物、语气、形状、字体、配色和图片处理。区分“用户明确的品牌”与“AI 建议”。文章的高饱和/玩具感只是示例，不作为每个 APP 的默认风格。

### 2. 页面结构与设计方向

列出屏幕矩阵：每屏一个主要任务、信息层级、关键动作、数据和必要状态，画出导航/返回/完成/取消路径。原型可用本地 SVG、HTML 或用户选定的白板，不强制 Lovart、Excalidraw 或 Figma。

已有品牌与 tokens 优先。新方向可检索 UI/UX Pro Max，再用当前实际可读的 Taste 规则推敲构图、布局、密度、字阶、品牌表达与截图迭代；若版本附有 APP 专用参考则读取它，缺失的参考/脚本按 integrations 降级，不虚构执行。两者结果由同一份项目 tokens 统一，不能反复轮流覆盖。原生行为由平台规范约束。只读审查可停在差距报告。

### 3. 多屏视觉与素材

需要生成图/图像方案时读 [prompts.md](references/prompts.md) 和 [media-tools.md](references/media-tools.md)。先列素材清单，再生成页面；跨屏保持相同 tokens、图标体系、IP 比例、光影和姿态逻辑。生成图用于视觉方向，不证明交互或文案准确。

吉祥物与插画保存为独立素材，需透明背景时在图像工具中明确设置透明背景，并查看实际 alpha。不要把整屏图片当可编辑组件。无图像工具时交付完整 prompts，图像阶段标 `not_executed`，仍推进不依赖图像的代码与规格。

### 4. 还原为可交互界面

保留项目技术栈、路由、数据和品牌约束；仅无项目且用户要求快速交互原型时可用本地 HTML/CSS/JS，并说明这是 Web 原型。参考图中的文本、按钮、输入、列表、导航做成真正组件，图片仅用于本应是图片的内容。

为实际存在的控件实现默认、按下/点击、焦点、禁用、加载等适用状态；hover 只用于支持指针的表面，触屏不能靠 hover 暴露核心操作。按屏幕任务连接导航、表单反馈和返回路径；演示数据明确标记，不伪造后台、支付或线上提交。

图标在项目已有体系中统一；没有时可参考原文 Hugeicons，再核对可用版本、许可、平台适配及是否需要密钥，不强行安装。图像中文字错误在代码中恢复为可读文本。

### 5. 看图、操作、修复

读 [quality-handoff.md](references/quality-handoff.md)。先抓同尺寸基线，按“结构与比例 → 字体/间距 → 素材与颜色 → 状态与细节”修复，再看最终渲染与操作证据。文章的 2–3 轮是经验，不是质量保证；不循环无新证据的微调。

在实际交付的窄/标准/大尺寸检查溢出、文本放大、安全区、键盘遮挡、触控和深浅主题（若支持）。原生 iOS 44pt、Android 48dp 的触控目标不能用 Web px 换算替代。使用适当自动检查与实际交互；只看截图不能证明交互/读屏/真机。

如任务要求审查或精修且 Impeccable 可用，按其 `audit`/`polish` playbook 执行，完整保留它对布局、文案、动效与边界的职责；不因其存在而重复重做方向。报告未修复项与原因。

### 6. 交接与验收

在既有项目载体记录屏幕矩阵、tokens、素材、代码入口、运行方式、截图、已验证交互和剩余项。没有载体时使用 `assets/brief-template.md` 和 `assets/delivery-template.json`；`studio.py init --output <新目录>` 可安全复制空模板，已有目标拒绝覆盖。

需要可编辑设计时先交付本地设计交接包，再使用实际可用、已授权的设计工具。原文的图片转设计稿与 Web to Figma 都是可选路径；本插件不内置这些第三方转换器。转换后核对独立文本、布局、组件/矢量及字体，并验证一次实际编辑。截图贴入 Figma 不算完成。

交付时分开说明：提示词 / 图像 / 可运行代码 / 浏览器验证 / 原生设备 / 可编辑设计。使用 `verified`、`partial`、`not_executed`、`needs_input`，附实际证据；任何未执行项不能写成 PASS。

## 按需资源

- 来源与方法映射：[article-method.md](references/article-method.md)。复核原文或解释改编时读。
- 技能发现、冲突与命令：[integrations.md](references/integrations.md)。复用四技能时读。
- 可选 SaaS 模式、已有项目策略与科技视觉：[saas-mode.md](references/saas-mode.md)。选择 SaaS 时读；可复制制作提示词见 [saas-prompt.md](assets/saas-prompt.md)。
- 宣传页、落地页、海报和商店截图：[marketing.md](references/marketing.md)。推广设计时读。
- Lovart / image 选择、参考图和结果检查：[media-tools.md](references/media-tools.md)。图像阶段按需读。
- 品牌、多屏、素材、还原和纠偏提示词：[prompts.md](references/prompts.md)。生成或还原时读。
- 最低质量标准、交互验证与设计交接：[quality-handoff.md](references/quality-handoff.md)。审查或交付时读。
- 本地辅助工具：`scripts/studio.py doctor`、`contrast <前景色> <背景色>`、`preset saas --tone tech-refined --scope auto --surface both`、`init --mode saas --output <新目录>`、`check <delivery.json>`。preset 仅生成设计配置，不生成图片或修改项目；check 只核验交接契约与文件存在性，不证明 UI 质量。
