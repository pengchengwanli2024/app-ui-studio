# Oil公开项目的适配与发现

本轮在2026-11-17对 [oil-oil公开仓库](https://github.com/oil-oil?tab=repositories) 分页盘点：121个仓库、73个非Fork、48个Fork；其中24个相关项目检查入口/README，另46个检查README摘要并保留提交定位；34个项目的方法映射到本插件、5个作为维护参考。其余按外部可选工具或参考分类，全部记录在assets/oil-projects.json；这不是所有上游工具都已安装、执行或验收的声明。

## 发现命令

```text
python3 "<技能目录>/scripts/studio.py" ecosystem
python3 "<技能目录>/scripts/studio.py" ecosystem --kind projects --id oil-icon
python3 "<技能目录>/scripts/studio.py" ecosystem --kind projects --disposition adapted-method
python3 "<技能目录>/scripts/studio.py" ecosystem --id icon-set
```

默认只列16个新增能力的简要路由，不把121份仓库资料注入提示词。项目目录保留来源、许可证据、Fork、审阅层次、处理理由和已审提交；entrypoint/readme表示检查相关指导入口，readme-excerpt表示检查README摘要而未深审其实现，metadata表示仅做元数据盘点；3个非Fork未找到常见README（其中1个空仓库），48个Fork只盘点归属与元数据。目录是离线快照，不联网更新、安装、激活或执行上游。

## 命中任务才加载

| 任务 | focus | 指导 |
|---|---|---|
| 前端状态、iOS依据、节点编辑器、业务旅程 | frontend / native-ios / node-editor / product-analysis | [product-implementation.md](product-implementation.md) |
| 校准还原、图标、解释图、语境方向 | mockup / icon-set / visual-explain / art-direction | [creative-assets.md](creative-assets.md) |
| 文案、术语、定位批注、README、交接 | copy / terminology / review-context / readme / handoff | [writing-handoff.md](writing-handoff.md) |
| 媒体随动、录屏演示、传播素材 | media-runtime / product-demo / campaign | [interactive-media.md](interactive-media.md) |

用workflow的focus生成单项提示词，审查用task=audit，只要构思/方案用task=brief，要求实际制作才进入design等实施任务；product-analysis与review-context默认audit，terminology默认brief，三者只支持audit/brief；原六专项和旧CLI保留。小程序使用platform=mini-program，建议视口待读取真实工程后确定，不冒称已在开发者工具或真机通过。

## 采用的是决策方法

统一接口、来源可追溯、先Pilot后批量、真实回执、可恢复状态与最小必要取证可以融入本插件。作者个人角色、配色、固定宫格、指定模型/供应商、安装路径、宿主Hook、审批设置和强制委托不能成为新的全局默认值；现行用户要求与宿主规则始终优先。

本包独立撰写指导与发现工具，未捆绑上游源代码、脚本、商标或素材。公开可见不自动表示许可相同：LICENSE、README声明和GitHub元数据分别记录；未确认项标UNKNOWN。需要实际调用外部技能时，检查当前安装、许可、能力与授权，再按其真实接口操作；缺少增强仍完成可独立交付部分。Fork不当成Oil原创能力或重新授权来源。
