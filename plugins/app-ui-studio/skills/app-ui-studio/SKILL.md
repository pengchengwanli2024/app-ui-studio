---
name: app-ui-studio
description: "用于设计、实现、精修或审查 APP / SaaS、内容页面与宣传页，以及配套图标、解释图、文案、演示与交接；支持存量改版、多屏一致性、前端状态和真实渲染验收。纯后端逻辑或无关整理不使用。"
---

# APP UI Studio

把品牌、用户任务、结构和素材贯穿到实际界面。说明跟随用户语言，界面文案跟随产品受众；未指定时使用简体中文。用户只要分析时交付分析；要求制作时持续到所需产物与适当验证完成。

## 先确定范围与页面任务

明确的小修改直接复用现有实现，样式变更看目标视口；只读审查不改文件，不因通用清单重开设计。新建、存量改版、改流程、加功能或多屏任务，按需读 [design-craft.md](references/design-craft.md)：先区分可改与锁定范围，再按每页实际任务选择工作区、内容浏览、说服页或操作体验。软件类型与行业不能替代页面领域。

默认深化一个推荐方向；只在用户明确要求比较时探索多个。已有品牌、tokens和已定方向继续沿用；精修改视觉、加功能沿用视觉系统，重塑以授权范围为准。用户已授权实施或说“你定／直接做”时持续完成，不因建议方案、素材选择或代表页检查重复停顿。

多屏任务先确定页面地图与全局导航，验证代表页及关键状态后再铺开。复用项目既有规范、变量与组件；单次小修改不额外生成规范、报告或交接文件。

改法已明确的文案、数量、单处颜色或间距，直接局部修改，不重开方向或完整流水线；样式变化只查看改动与相邻区域。只要提示词时交付提示词，只要评审时交分析并停止，不进入修正循环。

## 入口与能力发现

支持自然语言，或 `brief`、`prompts`、`design`、`saas`、`marketing`、`reconstruct`、`audit`、`polish`、`handoff`、`compare` 参数。这些是技能路由，不是 MCP 工具或独立命令。无参数时从用户目标继续，只在实质缺口阻碍结果时提问。没有新建项目指令时不因调用插件就生成模板。

需要专用软件类型、行业项目或批量提示词时，按需读 [prompt-library.md](references/prompt-library.md)，用 `studio.py catalog` 发现ID，再用 `prompt --software <id> --industry <id>` 组合，`export-prompts --output <新目录>` 导出20类软件＋16行业模板。只加载命中的配置，不把36份正文注入入口。SaaS是服务形态，功能类型和行业仍分别指定；要求制作时必须继续实现和实际验证，不能停在生成提示词。

2.2 新任务可用 `python3 scripts/studio.py workflow --task extend --domain workspace --scope existing --surface product` 生成按范围与领域组织的提示词；支持 design / polish / extend / reconstruct / audit。`--platform` 选择实际交付端，`auto` 留待读取项目后判断。此命令不检查或写入项目、不调用模型。原 `prompt` 与36份导出内容保持兼容；执行旧模板时仍以本入口的任务范围为准。

`saas` 是可选设计模式。用户选择 SaaS，或任务明确为 SaaS 产品时，读取 [saas-mode.md](references/saas-mode.md)，复用下述工作流。`scope=auto/new/existing/mixed` 决定如何处理项目现状，`surface=product/marketing/both` 决定交付面；未指定时先读项目推断。`tone=calm/tech-refined/tech-expressive` 控制视觉表达，SaaS 默认 `tech-refined`，其他模式保持原行为。科技风格遵从用户 brief，不把通用去装饰偏好当成对玻璃、光场或局部 3D 的绝对禁令；例外限定表面，仍检查可读性、交互和动效降级。

非 SaaS 项目指定“科技、酷炫、AI 智能体视觉”或 tech tone 时，可读取 [tech-visual-language.md](references/tech-visual-language.md) 作为视觉修饰，不改变业务模式、品牌或项目技术栈。

1. 确认目标目录、适用项目规范、工作树与现有 UI。区分原生 APP、移动 Web、桌面工作界面、营销页面；手机宽度不等于原生 APP。
2. 使用宿主暴露的技能清单解析技能目录；有本地执行能力时可运行 `python3 "<本技能目录>/scripts/studio.py" doctor --project "<项目目录>"`。按当前环境选择已安装的 Python 3；Windows 可用 `py -3` 或经核验的 `python`。doctor 仅检测文件与运行时，不证明技能已启用或引擎已运行。
3. 需要四技能增强时读 [integrations.md](references/integrations.md)，只加载当前阶段所需的实际 `SKILL.md`。不覆盖现有安装、不自动安装依赖、不改 hook。缺技能仍能按下述基础流程工作，并写明增强未执行。
4. 图像和设计工具以当前工具列表为准。需要 Lovart 或 image 时读 [media-tools.md](references/media-tools.md)，遵循宿主工具规范和现有授权。用户要求两者参与时，为两者分别分配实际产物，不能只调用一个就称已完成双方协作。按“素材计划 → 真实生成/编辑 → 查看并筛选 → 项目落地 → 组件接入 → 渲染验证”留证。缺能力时交付可用提示词并记录未执行阶段，不因安装本插件就生成图或产生付费任务。
5. `marketing` / 宣传页 / 落地页 / 海报请求读 [marketing.md](references/marketing.md)。APP 与宣传页同做时复用品牌和已完成屏幕；宣传图不能代替真实 APP 屏幕。仅宣传页任务不强制先制作完整 APP。

`compare` 用于冻结版本、同状态截图对比及技能迭代，按需读 [comparison.md](references/comparison.md)。读取并保存实际插件清单与入口哈希，不依赖会被刷新清理的缓存；基线、失败/UNKNOWN和原始回执保持不变。比较文件契约、实际渲染与视觉判断分别留证。

### 专项只在需要时加载

| 本次目标 | 按需指导 |
|---|---|
| Web代码质量、现代平台选择、性能或无障碍审计 | [modern-web.md](references/modern-web.md)：按问题检索与兼容降级，Lighthouse 实测、报告归因和条件可比性；不将实验室分数当视觉或业务验收 |
| 把单个控件或数据组件磨细 | [component-craft.md](references/component-craft.md)：拆分触发器、值、选项、状态与承载尺寸；工作区以功能为准，不强制实物主视觉 |
| 构思素材、套图或图像与页面的关系 | [media-tools.md](references/media-tools.md) 的素材构思：先定用途、身份、镜头与留白，再选复用/编辑/生成 |
| 操作反馈、状态切换或手感 | [motion-scroll.md](references/motion-scroll.md) 的动效编排：立即反馈、真实结果、打断与生命周期清理 |
| 品牌/宣传页的滚动过程表达 | 同文件的滚动叙事：先静态分镜，再绑定进度，提供手机、低动效与失败替代；后台和阅读页不默认叠加 |
| 明确比较多个方向或版式 | [exploration.md](references/exploration.md)：只做足以选择的片段，同状态比较后深化选中方向 |
| 看过成果后继续回改 | [iteration.md](references/iteration.md)：意见转假设、保留确认项、前后对照与方向问题诊断 |
| 设计稿单位校准、小程序、成套图标或解释图 | [creative-assets.md](references/creative-assets.md)：mockup / icon-set / visual-explain / art-direction，只读取对应部分 |
| 前端状态、iOS依据、节点编辑器或产品旅程 | [product-implementation.md](references/product-implementation.md)：frontend / native-ios / node-editor / product-analysis |
| 文案、术语、定位批注、README与交接 | [writing-handoff.md](references/writing-handoff.md)：copy / terminology / review-context / readme / handoff |
| 视频/帧序列随动、真实演示或传播素材 | [interactive-media.md](references/interactive-media.md)：media-runtime / product-demo / campaign |

`python3 scripts/studio.py workflow --focus component` 可生成专项提示词；focus可选component / media / motion / scroll / explore / iterate，每次一个，仍服从task、领域和锁定范围。explore可带 `--directions 3`，audit只输出观察维度，不实施。`python3 scripts/studio.py board <manifest.json> --output <新目录>` 制作已有PNG/JPEG截图的本地选择页，不生成候选、不评分或自动应用选择；格式见 [comparison.md](references/comparison.md)。

用户只要方案、素材构思或提示词时，使用 `workflow --task brief --focus media` 等相应专项；brief输出方案，关闭产品写入与实现意图，不因默认design模式带出制作整站或生成素材。用户实际要求制作时才用design等实施任务。

`python3 "<技能目录>/scripts/studio.py" ecosystem` 离线发现新增16个专项及默认任务，`ecosystem --kind projects --id <仓库名>` 查看来源、许可证据与适配层次，详见 [oil-ecosystem.md](references/oil-ecosystem.md)。product-analysis与review-context默认audit，terminology默认brief，这三项只支持audit/brief；其余专项仍按用户要求选任务。文案、素材与交接只完成对应对象，不自动展开整站。小程序可用 `--platform mini-program`，平台验收须实际执行。

这是一组独立撰写的方法适配和来源目录，未内置上游应用或执行器。仅当任务需要实际外部工具时，核对安装、版本、许可及授权后使用；不自动安装、注入页面、改变宿主设置或发布内容。其他仓库的个人风格、模型供应商和Fork归属不成为本插件默认值。

需要把反馈交给开发者时，board可按截图保存整图意见与位置批注，切换候选不重绑旧意见；支持点击/键盘定位、本标签页草稿和JSON导出。用 `studio.py board-feedback <board.json> <feedback.json>` 核对真实截图字节和位置归属，再进入回改；检查通过不代表建议正确或修改已执行，详见 [comparison.md](references/comparison.md)。

`workflow --focus web-quality` 默认只读审计；需要修改时显式选择本轮 task。`studio.py web-report <lhr.json> --baseline <old-lhr.json>` 只读提取 Lighthouse 指标和比较条件，不启动浏览器、不认证视觉质量；具体用法和数据边界见 [modern-web.md](references/modern-web.md)。

## 按目标选择阶段

完整新设计按以下依赖推进；已有品牌、代码或参考图时从对应阶段切入，复用既有产物。提示词任务完成于可用 prompts；审查任务不修改代码。不要为了凑阶段重做已有设计。

### 1. 品牌与任务

记录产品、用户、主要任务、目标平台、页面、品牌、参考素材及交付格式。优先读项目现有需求与设计系统；不要创建相互竞争的事实源。缺省且易回退的事项标为假设继续。

品牌定义保留 logo、吉祥物、语气、形状、字体、配色和图片处理。区分“用户明确的品牌”与“AI 建议”。文章的高饱和/玩具感只是示例，不作为每个 APP 的默认风格。

### 2. 页面结构与设计方向

列出屏幕矩阵：每屏一个主要任务、信息层级、关键动作、数据和必要状态，画出导航/返回/完成/取消路径。原型可用本地 SVG、HTML 或用户选定的白板，不强制 Lovart、Excalidraw 或 Figma。

多页补上页面领域、入口与所沿用的代表页，先固定共享导航，再做代表性任务与风险状态。内容浏览让对象先出现，工作区让判断与动作相邻，宣传页围绕价值与证据构图；不把同一后台骨架套给所有页面。检查过代表页，再提取共享组件并分批铺开。

已有品牌与 tokens 优先。新方向可检索 UI/UX Pro Max，再用当前实际可读的 Taste 规则推敲构图、布局、密度、字阶、品牌表达与截图迭代；若版本附有 APP 专用参考则读取它，缺失的参考/脚本按 integrations 降级，不虚构执行。两者结果由同一份项目 tokens 统一，不能反复轮流覆盖。原生行为由平台规范约束。只读审查可停在差距报告。

### 3. 多屏视觉与素材

需要生成图/图像方案时读 [prompts.md](references/prompts.md) 和 [media-tools.md](references/media-tools.md)。先列素材清单，再生成页面；跨屏保持相同 tokens、图标体系、IP 比例、光影和姿态逻辑。生成图用于视觉方向，不证明交互或文案准确。

吉祥物与插画保存为独立素材，需透明背景时在图像工具中明确设置透明背景，并查看实际 alpha。不要把整屏图片当可编辑组件。无图像工具时交付完整 prompts，图像阶段标 `not_executed`，仍推进不依赖图像的代码与规格。

### 4. 还原为可交互界面

保留项目技术栈、路由、数据和品牌约束；仅无项目且用户要求快速交互原型时可用本地 HTML/CSS/JS，并说明这是 Web 原型。参考图中的文本、按钮、输入、列表、导航做成真正组件，图片仅用于本应是图片的内容。

为实际存在的控件实现默认、按下/点击、焦点、禁用、加载等适用状态；hover 只用于支持指针的表面，触屏不能靠 hover 暴露核心操作。按屏幕任务连接导航、表单反馈和返回路径；演示数据明确标记，不伪造后台、支付或线上提交。

涉及保存、批量、外部执行或重试时，区分处理中、成功、失败与结果未知；核对回执、可安全重试的范围及部分成功恢复。切换筛选和打开/关闭详情后保留查询、滚动与焦点；保存后刷新或读回核对结果。

图标在项目已有体系中统一；没有时可参考原文 Hugeicons，再核对可用版本、许可、平台适配及是否需要密钥，不强行安装。图像中文字错误在代码中恢复为可读文本。

### 5. 看图、操作、修复

读 [quality-handoff.md](references/quality-handoff.md)。先抓同尺寸基线，按“结构与比例 → 字体/间距 → 素材与颜色 → 状态与细节”修复，再看最终渲染与操作证据。文章的 2–3 轮是经验，不是质量保证；不循环无新证据的微调。

在实际交付的窄/标准/大尺寸检查溢出、文本放大、安全区、键盘遮挡、触控和深浅主题（若支持）。原生 iOS 44pt、Android 48dp 的触控目标不能用 Web px 换算替代。使用适当自动检查与实际交互；只看截图不能证明交互/读屏/真机。

多屏捕获检查干净首次加载与实际导航后的状态；hash 路由核对锚点滚动是否裁掉头栏。保留有效键盘焦点样式，不用隐藏异常美化截图。

如任务要求审查或精修且 Impeccable 可用，按其 `audit`/`polish` playbook 执行，完整保留它对布局、文案、动效与边界的职责；不因其存在而重复重做方向。报告未修复项与原因。

### 6. 交接与验收

需要交接包时，在既有项目载体记录屏幕矩阵、tokens、素材、代码入口、运行方式、截图、已验证交互和剩余项。没有载体时可用 `assets/brief-template.md` 和 `assets/delivery-template.json`；`studio.py init --output <新目录>` 可安全复制空模板，已有目标拒绝覆盖。普通局部修改最终简述即可。

需要可编辑设计时先交付本地设计交接包，再使用实际可用、已授权的设计工具。原文的图片转设计稿与 Web to Figma 都是可选路径；本插件不内置这些第三方转换器。转换后核对独立文本、布局、组件/矢量及字体，并验证一次实际编辑。截图贴入 Figma 不算完成。

交付时分开说明：提示词 / 图像 / 可运行代码 / 浏览器验证 / 原生设备 / 可编辑设计。使用 `verified`、`partial`、`not_executed`、`needs_input`，附实际证据；任何未执行项不能写成 PASS。

## 按需资源

- 来源与方法映射：[article-method.md](references/article-method.md)。复核原文或解释改编时读。
- 范围分流、页面领域、代表页铺开与设计规范：[design-craft.md](references/design-craft.md)。新建、存量改版或多屏任务按需读。
- 技能发现、冲突与命令：[integrations.md](references/integrations.md)。复用四技能时读。
- 可选 SaaS 模式、已有项目策略与科技视觉：[saas-mode.md](references/saas-mode.md)。选择 SaaS 时读；可复制制作提示词见 [saas-prompt.md](assets/saas-prompt.md)。
- 宣传页、落地页、海报和商店截图：[marketing.md](references/marketing.md)。推广设计时读。
- Lovart / image 选择、参考图和结果检查：[media-tools.md](references/media-tools.md)。图像阶段按需读。
- 品牌、多屏、素材、还原和纠偏提示词：[prompts.md](references/prompts.md)。生成或还原时读。
- 最低质量标准、交互验证与设计交接：[quality-handoff.md](references/quality-handoff.md)。审查或交付时读。
- 版本冻结与同状态对比：[comparison.md](references/comparison.md)。
- 本地辅助工具：`scripts/studio.py doctor`、`contrast <前景色> <背景色>`、`preset saas --tone tech-refined --scope auto --surface both`、`init --mode saas --output <新目录>`、`check <delivery.json>`。preset 仅生成设计配置，不生成图片或修改项目；check 只核验交接契约与文件存在性，不证明 UI 质量。

2.1 本地比较命令：`scripts/studio.py compare <baseline.json> <candidate.json> [--output <新报告.json>]`。仅检查版本标签、目录内证据、业务/品牌哈希和 PNG/JPEG 头部尺寸；始终 `visual_quality_verified=false`，不证明提供方执行、截图真实性或视觉提升。`catalog` / `prompt` / `export-prompts` 保留2.0命令与36类配方。
