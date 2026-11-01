# Harness² 有界迭代记录

本轮升级从冻结的插件 1.2.0 开始，交付源码版本为 1.3.0。实验只评估新增 `compare` 文件契约和执行指导，不把它当作完整 APP 生成或视觉质量评测。

run `24e4c378711f489888725ac7`，同一冻结任务、工具和检查器，k=1。四次执行分别使用独立新上下文；请求模型参数为 `gpt-6.1-sol`、reasoning `medium`。这是实际提交参数，不是提供商内部模型遥测认证。

| 条件 | 最终契约检查 | 独立最终验证 | 选择 |
| --- | --- | --- | --- |
| baseline | 42/42，exit 0 | 34/34，exit 0 | 采用 |
| general | 42/42，exit 0 | 未单独执行 | 保留证据 |
| domain | 42/42，exit 0 | 未单独执行 | 保留证据 |
| composed | 42/42，exit 0 | 未单独执行 | 保留证据 |

四路最终结果没有可测优势，因此保守采用 baseline，`proven_general_gain=false`。过程差异也保留：general 曾在补丁尚未产出时提前调用检查器，属于准备失败；domain 首次实现因 JPEG 后续结构解析过严未通过，调整到约定的头部与尺寸边界后通过。其余自报补充测试不合并为统一评分，也不据此宣称因果增益。

## 证据与重放

[summary.json](../evidence/harness/summary.json) 保留冻结输入哈希、四份补丁哈希、结果和限制。各条件补丁、最终检查输出及独立验证输出在 [evidence/harness](../evidence/harness/)。原始运行、失败轨迹和账号回执仍留在本地，不公开原始会话或账户信息。

```bash
python3 scripts/replay_harness.py
```

该命令只在临时目录重放保留的代码检查，需要系统 `patch`；不再调用模型、不新增实验，也不替代原始时间点的结果。公开基线脚本来自冻结 1.2 源码，未修改原始检查器。

## 已知限制与应用后的验证

冻结 JPEG fixture 的 base64 比原始自制像素 JPEG 多出六个 SOF 后字节，系统图像工具仍可解码。原 fixture、检查器与原结果全部保留，不以修改测试制造通过。四路另外使用相同的真实浏览器 JPEG 和实际 Lovart PNG 补验：可比 exit 0、伪造尺寸 exit 2、状态变化 exit 1，全数符合契约。这仍然只是图片头部尺寸检查。

集成后另外增加两处 `RuntimeError` 捕获，兼容旧版 Python 的符号链接循环异常；它是补丁采用后的可审查修正，不冒充原始四路实验中的代码。发布源码使用纠正的自制 JPEG fixture 在 Python 3.11、3.13、3.14 分别通过 42 项公开测试。

实际栖刻清单和浏览器验证见 [实测报告](TEST_REPORT.md)。`compare` 始终输出 `visual_quality_verified=false`。本轮只说明当前任务的行为；不证明普适技能增益、完整图片解码、截图来源、原生设备、可编辑设计或正式产品验收。

公开预检脚本的首次实现另有一次 `IndentationError`，已修正后重新执行通过；对应外层 failed 事件原样保留，不混入冻结四路实验得分。主控应用后的新一轮检查绑定全部六个当前输入哈希，原生反馈返回 `verified_post_apply_closeout`、failure_streak=0，见 [收口与先前失败](../evidence/harness/closeout.json)。
