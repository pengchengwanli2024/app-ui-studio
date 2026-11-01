# 2.1.0：合并能力与栖刻回归

验证日期：2026-11-02，Asia/Shanghai。2.1基于账号当前2.0.0完整源码，合入已发布1.3.0的版本冻结、同状态取证与比较能力。账号插件、公开源码和安装包保持同一版本；原1.1/1.2示例与1.3发布证据不覆盖。

## 合并保留了什么

| 能力 | 结果与证据 |
| --- | --- |
| 20类软件、16行业 | 两份catalog字节SHA保持2.0原值，全部ID与实际CLI输出一致 |
| prompt组合 | 36个单独软件/行业输出、20个双维组合与冻结2.0输出一致；20组配对覆盖全部软件和16行业，不是320全矩阵 |
| export-prompts | 36份Markdown正文逐份匹配2.0哈希；已有目录、文件、符号链接和缺失父目录均不会被覆盖/自动创建 |
| 导出版本 | prompt_library只将导出清单版本字面值2.0.0改为2.1.0；归一后整文件SHA仍等于2.0 |
| 既有CLI | doctor/contrast/init/preset/check与catalog/prompt/export-prompts保留；compare接入且全部9条命令可在实际`--help`发现 |
| compare | 比较实现块与1.3字节相同，原42项契约断言保留；始终`visual_quality_verified=false` |
| 技能流程 | 保留2.0按需配方、行业边界与共享决策；保留1.3媒体复用、失败证据和初始hash路由检查 |
| 插件身份 | 名称、三条defaultPrompt及顺序保持；账号包保留原作者/展示信息，公开包用contributors脱敏 |

[能力保留清单](../evidence/v2.1.0/merge-preservation.json) · [原2.0源哈希](../evidence/v2.0.0/source-hashes.json) · [独立冻结的CLI期望](../tests/fixtures-v2.json)

打包器现在排除Python运行生成的缓存，不删除工作树缓存，并继续拒绝符号链接。新增模块被真实运行后仍能安全打包；代码与素材不会混入`__pycache__`或`.pyc`。

## 同一个栖刻怎样实测

实际调用2.1 `prompt --software personal-productivity --scope existing --surface both --tone tech-refined`，行业留空，因为个人专注示例没有行业约束。原始组合器输出见 [qike-prompt.json](../evidence/v2.1.0/qike-prompt.json)，绑定产品事实后的执行输入见 [qike-execution-brief.md](../evidence/v2.1.0/qike-execution-brief.md)。未改写组合器的`project_inspected=false`等字段来冒充执行；实际结果单独记录。

已有业务和视觉得到保留：三屏、任务、新增/撤销完成、15/25/45分钟选择、计时、记录、本地存储和宣传页。通用配方中的日期、重复规则、跨设备同步没有被强加进这个本地示例。`app.js`、CSS、品牌小芽及Lovart主视觉均沿用合格实现；宣传页内嵌屏幕换为本轮重新捕获的实际截图。

- 三屏宽320/390/430，宣传页宽320/390/430/1280/1440，共14组：无横向溢出、坏图、重复可见H1或小于44 CSS px的有效控件。
- 三路由干净首次加载及1440×1050三iframe均headerTop=0、scrollY=0；三屏新截图与宣传页桌面/手机截图实际查看。
- 实际12组操作：宣传锚点/CTA、本机空状态、键盘拒绝空白、任务新增后刷新、完成撤销、15分钟自然递减、暂停刷新、继续/取消结束、结束生成不到1分钟的本机记录、记录刷新和过滤、Tab焦点、5个对照选项。
- [可交互比较页](../examples/qike/comparison-2.1.html) · [机器比较结果](../evidence/comparison-2.1.json) · [三屏截图](../evidence/v2.1.0/app-three-screens.jpg) · [桌面宣传页](../evidence/v2.1.0/marketing.desktop.jpg) · [手机宣传页](../evidence/v2.1.0/marketing.mobile.jpg)

文件契约可比不代表像素控制实验。历史基线来自Chrome，本轮为独立Playwright Chromium；保留既有设计而重新捕获的字节差异不解释为视觉提升。

## 技能、素材与失败证据

本轮实际读取UI/UX Pro Max、Mobile App Design、Taste和Impeccable的适用入口；UI/UX实际查询`focus not obscured`，保留AA/AAA区别。Mobile用于Web层级、导航和控件审查，不换算原生单位。当前Taste明确不覆盖多步骤产品UI，只对宣传页按已确认品牌审查。Impeccable context与audit检测实际执行，exit2的4条warning保留并审查，没有关闭全局规则制造零警告。[技能审查](../evidence/v2.1.0/skills-review.json) · [检测原文](../evidence/v2.1.0/impeccable.json)

image方向稿、小芽和Lovart主视觉沿用1.2已验证资产，本轮新生成调用数为0；没有拿复用素材冒充新生成。原媒体回执与来源保持，四项上游技能仍只列依赖、不复制入仓库。

首次营销测量把屏外懒加载图片当成坏图；实际滚动并解码后完整重查通过。另一文本正则检查未识别计时，独立DOM/可访问性快照显示计时正常，改读实际命名计时状态后完整新上下文回归通过。两项属于同一实现候选的检查失败，原始日志保留，公开 [失败与修正说明](../evidence/v2.1.0/browser-initial-failure.json)。没有修改产品代码掩盖失败。测试fixture准备时另曾把额外README计入模板数量，按36份真正模板重建，未减少有效正文断言。

Harness²本轮实际完成context、assess和feedback，standard → skip，复用同项目1.3经验；没有重跑、改写或冒充原四路实验。最终34个源/检查输入哈希前后保持，新的passed反馈failure_streak=0。[反馈摘要](../evidence/v2.1.0/harness-feedback.json)

## 本地与账号验证

Python3.11、3.13、3.14各自通过42项原契约和6组兼容检查；预检15项通过，JS语法和ZIP CRC通过。28文件安装包排除运行时缓存。[验证与安装包哈希](../evidence/v2.1.0/validation-summary.json)

账号插件已通过带当前release保护的更新保存为2.1.0，USER/PRIVATE保持。写回后重新读取全部28个文件：支持文件字节一致、清单语义一致；直接执行回读源码的catalog和compare通过。Codex安装缓存已更新2.1，实际执行缓存中的prompt与compare也匹配公开结果。[账号/安装验证](../evidence/v2.1.0/account-verification.json)

公开源码、Release附件及校验值随本次提交发布，远端CI和附件回读结果以GitHub运行/Release为发布回执。旧v1.3.0标签与附件保留。

未验证原生真机、系统键盘遮挡、完整读屏、完整15/25/45分钟自然结束、Figma可编辑图层或Windows环境。示例记录不是用户真实数据；没有普适技能或审美提升结论。
