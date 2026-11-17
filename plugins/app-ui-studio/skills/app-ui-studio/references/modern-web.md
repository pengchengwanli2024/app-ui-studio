# 现代 Web 实施与实测质量

涉及 Web 性能、语义与无障碍、现代 CSS、浏览器 API 或兼容性决策时按需读取。普通文案/间距小改沿用项目，不强制联网、安装或跑全站审计；原生 APP 的平台验收另做。

## 先定位能力，再选择技术

把用户任务转成具体平台能力，例如 `responsive component layout`、`modal dialog focus`、`optimize image priority`。已有 Modern Web Guidance CLI 时，搜索一个能力，再读取命中的指南；未安装时可读其公开指南或对应官方文档，无需为了查询修改技能安装、宿主策略或项目依赖。

```sh
npx modern-web-guidance@latest search "optimize image priority"
npx modern-web-guidance@latest retrieve "optimize-image-priority"
```

上例会取用注册表软件，只有任务需要且允许时执行。记录实际 CLI/指南版本与读取内容，不把搜索结果、功能目录或安装成功当实现验证。没有命中时改写一次具体能力，不把全部指南注入上下文。

浏览器支持采用实施时的 Baseline/MDN/目标端数据；区分 widely / newly / limited，以及项目真正使用的 WebView、Safari/iOS 和嵌入环境。Baseline 是决策输入，不能保证所有用户设备支持。新 API 先做 `@supports`、能力检测或原生 HTML 的可用基础，再按需要增强；不因新技术存在就替换成熟组件或添加大包。

| 实际问题 | 实施选择 | 验证重点 |
|---|---|---|
| 同一组件出现在不同容器 | 原有 grid/flex；确需随承载宽度变化时用容器查询、逻辑属性和有界字阶 | 容器而非仅窗口断点；长内容、字体放大和键盘焦点 |
| 对话框、菜单、披露与表单 | 区分阻断式 dialog、非模态 popover、details 与原生输入 | 语义名、可见名称一致、关闭/返回、焦点与滚动；不重复造焦点陷阱 |
| 首屏与长页图像 | 依据实际 LCP 候选安排优先级；保留尺寸/比例，合适格式与响应式资源 | 不懒加载 LCP；不要给所有图高优先级；普通折下图按需加载 |
| 卡顿与频繁布局 | 先区分输入等待、处理和绘制；批量读几何再写 DOM | 实际交互与性能记录，不能把所有延迟归因于事件处理器 |
| 已测得的长任务 | 按时间预算分块；适用时检测 `scheduler.yield()` 并提供退路 | 取消、重入、结果顺序；没有长任务证据不为普通循环加调度框架 |
| 动态与隐藏状态 | 沿用动效专项，检查初始可见性、隐藏暂停与清理 | 系统减少动态效果、恢复、反向与无脚本基础；不依赖动画完成业务 |

容器查询、popover、scheduler 等各有不同支持范围，分别检查；不要复制某一指南中与本任务无关的默认样式、供应商、遥测或通用强制步骤。

## 用 Lighthouse 找问题，再回到真实任务

已有 Lighthouse 时使用项目锁定版本，并核对该版本的 Node engines、Chrome 与运行方式。未安装或无浏览器时标记未运行，不伪造审计报告。独立审计进程使用隔离浏览器资料；不要接入用户正在使用的登录配置、关闭沙箱或默认清理真实账户站点。

```sh
# 先准备已有的报告目录，再审计允许访问的本地构建。
lighthouse http://127.0.0.1:8857/ --chrome-flags="--headless=new" --only-categories=performance,accessibility,best-practices,seo --output=json --output-path=reports/mobile.json
# 桌面另测，不能直接与手机分数作前后比较。
lighthouse http://127.0.0.1:8857/ --preset=desktop --chrome-flags="--headless=new" --output=json --output-path=reports/desktop.json
```

导航审计检查一次加载；已展开菜单、弹窗、表单状态需要对应 snapshot 或实际操作检查，交互时间段用 timespan。timespan/snapshot 没有的导航分数与 LCP 不补成零；冷启动导航的 TBT 也不能冒充真实用户 INP。需要线上体验判断时，另以获准的实地数据与交互归因支持，不自动加入采集或上报服务。

先保存同状态基线，再改有证据的问题：可达性和错误 → 布局稳定/响应 → 大资源与关键路径 → 局部执行开销。保留品牌、素材身份、主要任务和语义，不能靠隐藏内容、删除重要说明或只取最好的一次报告抬分。

性能比较记录 URL/数据状态、构建与资源、Lighthouse/浏览器版本、视口/设备、节流、区域设置和缓存策略。在同一机器上串行运行；需要归因时重复取中位数并保留范围，不并行压同一机器。CI 上的可变分数适合作诊断，固定预算应由项目基线决定，不能把全项目统一设为100分门槛。审美、保存链路、读屏/键盘与真机验收仍独立报告。

## 本地报告交接

```sh
python3 "<skill-base>/scripts/studio.py" workflow --focus web-quality --platform mobile --format json
python3 "<skill-base>/scripts/studio.py" web-report reports/mobile.json --baseline reports/baseline.json --output reports/summary.json
```

`web-quality` 默认只读 audit；要求修改时明确使用 polish / extend / design，沿用本次授权。它只生成提示词，不读取或修改项目。

`web-report` 只导入一个 Lighthouse LHR JSON（navigation/timespan/snapshot），不执行浏览器、联网或改产品。flow 容器需先按步骤导出单个 LHR。摘要保留类别分数、指标单位、失败项和未知；不转抄原始 DOM、请求头与 URL 查询值。手工、不可用、运行错误和真实零值分开；缺失 INP 不填零。

比较检查报告中的 URL（包含未输出的查询）、版本、设备/节流、浏览器、语言、缓存策略和审计范围/权重；条件缺失或不同则不算差值。条件匹配仍不证明用户状态或数据相同，交付者需核对实际场景。退出0表示导入契约有效，**不表示审计全通过**；1表示运行/审计错误或比较条件不匹配；2表示输入/输出无效。`--output` 只创建新文件，不覆盖已有文件或写穿输出符号链接。

## 从源码维护方法中吸收什么

Modern Web Guidance 源码将使用场景、指南、正例、预期和负例联系起来，并携带功能支持信息。适配到项目时，把最关键建议转成可观察结果：按钮可达、弹窗可退、图像不跳、失败有恢复，保留能暴露问题的反例。只匹配源码里的单词或 API 名称不足以证明行为正确；也不照搬上游的内部账户、模型配置和评测基础设施。

三项来源、固定提交与本次抽样边界见 [web-quality-sources.json](../assets/web-quality-sources.json)。这是独立编写的方法与报告工具；未捆绑上游技能正文、执行器、品牌素材或 Lighthouse 运行时，未声称完整审计全部项目。
