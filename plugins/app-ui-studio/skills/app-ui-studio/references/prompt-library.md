# 软件类型与行业提示词库

按需读取，禁止在每次入口加载全部配置。软件类型描述用户完成什么任务；行业描述术语、角色、证据与边界；SaaS是服务形态，不能替代功能分类。本库为实用覆盖清单，不是市场份额排名。

## 使用

自然语言例：`$app-ui-studio 为已有制造业项目新增AI协作工作台和宣传页，software=ai-agent industry=manufacturing scope=mixed surface=both tone=tech-refined`。

只要提示词时使用 `prompts`；要求制作时，先组合提示词再执行当前阶段，不把输出提示词当界面交付。

```text
python3 "<技能目录>/scripts/studio.py" catalog --kind all
python3 "<技能目录>/scripts/studio.py" prompt --software ai-agent --industry manufacturing --scope mixed --surface both --tone tech-refined
python3 "<技能目录>/scripts/studio.py" export-prompts --output "<不存在的新目录>"
```

Windows使用实际可用Python，例如 `py -3.11`。脚本无第三方依赖。`prompt --format json`含明确未检查项目、未执行生成与未验证UI标记。组合器不读取目标项目，不调用四技能或生成工具；智能体必须在实际执行中完成这些动作。

20类软件见 `assets/software-types.json`；16行业见 `assets/industry-profiles.json`。不把所有配置变成技能入口。已有项目保留架构、导航和设计语言；仅宣传页不实施后台工作流。未提供软件类型时按实际项目补全，不能把行业固定成某一种后台。

## 共享决策与冲突处理

复用项目现有设计文档，至少记录目标与范围、平台、屏幕矩阵、tokens及来源、组件状态、素材任务和验证缺口。没有现状时才新增一份决策文档。每个技能只补充其阶段的证据和决定，不完整重做其他技能。

优先级：当前用户明确要求与项目事实 → 平台行为和可访问性 → 项目已确认tokens → 检索建议与审美偏好。无法同时满足的实质冲突标出并处理，不能悄悄覆盖。Taste可审结构，不把它永久限制为上色；本次用户锁定结构时则保留结构。科技表达集中在适合的表面，不能借此降低表格可读性或伪造智能体执行。

阶段完成需要证据：UI/UX搜索查询和采用条目；Mobile的平台与控件检查；Taste实际加载、方向/截图迭代；Impeccable渲染后的定位清单与修复复验。缺失的能力如实降级，不增加固定审批或自动依赖安装。

## 验证层次

1. 本地组合器：配置完整、参数改变结果、非法ID拒绝、导出不覆盖/不越界、旧CLI兼容。
2. Harness²：独立工作区中的目标任务、候选、真实子进程轨迹、选择与采纳记录。区分确定性adapter与API模型改进器；前者不能证明视觉审美提升。
3. 实际设计任务：由组合prompt驱动实现，用实际工具生成并查看素材，接入真实组件，启动后检查截图与交互。合成数据不等于生产部署；文件契约通过不等于实际UI通过。

配方库、共享编排和回归按证据迭代；不自动覆盖四个上游技能，也不将本机日志、凭据或生成大图打包进插件。
