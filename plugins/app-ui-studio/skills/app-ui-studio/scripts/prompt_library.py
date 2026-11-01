"""On-demand, deterministic prompt composition; no provider or model execution."""
import argparse
import json
import re
import shutil
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SCOPES = ("auto", "new", "existing", "mixed")
SURFACES = ("product", "marketing", "both")
TONES = ("calm", "tech-refined", "tech-expressive")


def profiles(kind):
    filename = "software-types.json" if kind == "software" else "industry-profiles.json"
    data = json.loads((ASSETS / filename).read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or not isinstance(data.get("profiles"), list):
        raise ValueError("Unsupported catalog schema")
    records = data["profiles"]
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", record["id"], flags=re.ASCII):
            raise ValueError("Catalog IDs must be safe lowercase slugs")
        if record["id"] in ("con", "prn", "aux", "nul") or re.fullmatch(r"(?:com|lpt)[0-9]", record["id"]):
            raise ValueError("Catalog ID is a reserved filesystem name")
    ids = [p["id"] for p in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate catalog IDs")
    return records


def resolve(kind, identifier):
    if identifier is None:
        return None
    for record in profiles(kind):
        if record["id"] == identifier:
            return record
    raise ValueError(f"Unknown {kind} ID: {identifier}")


def compose(software=None, industry=None, scope="auto", surface="both", tone="tech-refined"):
    if scope not in SCOPES or surface not in SURFACES or tone not in TONES:
        raise ValueError("Invalid project scope, surface or tone")
    if not software and not industry:
        raise ValueError("Specify --software and/or --industry")
    sw, ind = resolve("software", software), resolve("industry", industry)
    scope_text = {
        "auto": "先检查当前目录和工作树，自行判断新建/已有/混合；不明时按已有项目只读调查，再做最小改动。",
        "new": "新建项目：依据目标平台和主任务选择必要且可维护的技术方案、页面结构和验证入口，不先堆依赖。",
        "existing": "已有项目：先读适用 AGENTS.md、架构、工作树、tokens、组件库和截图，沿用技术栈，保护已有改动，不顺手重构。",
        "mixed": "混合项目：先调查已有架构与设计语言，再新增页面；复用导航、tokens和组件，不引入第二套风格。",
    }[scope]
    surface_text = {
        "product": "只交付产品界面及其必要素材，不扩展营销站；优先主要任务、信息密度与可操作性。",
        "marketing": "交付宣传页及其素材：受众、价值主张、能力解释、可信证据与行动路径；不强制先造完整后台。不得编造客户、收益、认证与评价。",
        "both": "交付产品工作流与宣传页；共用品牌、tokens和真实完成的产品截图。宣传页说明能力与边界，不能拿宣传图代替可操作界面。",
    }[surface]
    tone_text = {
        "calm": "专业、精致、友好：清晰字阶与网格，中性底色、有限品牌强调和一致状态；减少装饰，保障高密度任务可读。",
        "tech-refined": "克制科技：精密网格、清晰字阶、细边界和局部光场；状态与真实数据驱动动效。工作区保持可读，主视觉可用有限玻璃或3D；不默认紫色渐变。",
        "tech-expressive": "鲜明科技：在首屏和关键能力演示使用空间层次、定向光场、受控3D或流动轨迹；业务表格和表单保持稳定。动效解释任务过程，不制造假的智能体活动。",
    }[tone]
    lines = ["# APP UI Studio 专用项目提示词", "", "你是产品设计师兼前端实现工程师。说明使用简体中文；要求制作时交付可运行、可查看的界面。",
             "", "## 项目输入", "产品目标：[填写产品、用户、主要任务；缺失时标注低风险假设继续]",
             "必须保留/避免：[填写品牌、页面、技术约束]", "参考资料：[填写链接、截图或本地路径；先实际读取]",
             f"软件类型：{sw['label'] if sw else '依据项目实际功能确定，不把行业名称当软件类型'}",
             f"行业：{ind['label'] if ind else '通用；有行业约束时以现有需求和可靠依据补充'}",
             f"scope={scope}；surface={surface}；tone={tone}", "", "## 范围与方向", scope_text, surface_text, tone_text,
             "软件类型和用户主任务决定功能范围；下列软件与行业条目均为待裁剪的检查候选。行业流程/交互只采用与主任务相关者，其余仅作术语和证据背景，不能为了覆盖清单新增行业作业模块；行业真实性、权限与安全边界始终保留。例如制造企业HR不新增BOM工单，工业安全LMS不新增现场整改系统。"]
    for record, title, keys in (
        (sw, "软件任务与界面", ("primary_users", "core_workflows", "screen_patterns", "state_checks", "ux_rules", "interaction_tests", "visual_focus")),
        (ind, "行业流程与边界", ("terms", "primary_users", "core_workflows", "required_evidence", "ux_rules", "interaction_tests", "boundaries")),
    ):
        if not record:
            continue
        lines.extend(["", f"## {title}", record["summary"]])
        labels = {"primary_users":"用户", "core_workflows":"核心流程", "screen_patterns":"屏幕结构", "state_checks":"状态", "ux_rules":"UX规则", "interaction_tests":"实际交互验收", "visual_focus":"视觉重点", "terms":"术语", "required_evidence":"所需证据", "boundaries":"边界"}
        for key in keys:
            if surface == "marketing" and key in ("screen_patterns", "state_checks", "interaction_tests"):
                continue
            qualifier = "（仅主任务相关候选）" if record is ind and key in ("core_workflows", "interaction_tests", "required_evidence") else ""
            lines.append(f"{labels[key]}{qualifier}：" + "；".join(record[key]))
    if surface == "marketing":
        lines += ["仅宣传页的业务流程与术语用来约束文案和能力示意，不要求实现后台、行业作业或完整业务数据。实际验收为：导航/锚点可达、CTA通向有效演示或明确联系渠道、表单验证与反馈真实且标注提交边界。无实际渠道则使用本地演示入口，不伪称已提交。"]
    lines += ["", "## 四技能共享决策与执行", "先建立一份共享设计决策：目标、屏幕矩阵、tokens、组件与状态、来源和待验证项；沿用项目现有载体，不重复创建事实源。",
              "1. 实际加载 $ui-ux-pro-max 的 SKILL.md 并运行适用检索，统筹UX与设计系统；报告检索条目和采用理由。数值来源可为技能、平台规范或项目tokens；新提案明确标为提案并实际验证，不冒称规范。",
              "2. 实际加载 $mobile-app-design，处理移动结构、导航、安全区、触控和原生规范；Web沿用区块→组件→状态方法。平台要求分别核对，不把手机宽度当原生APP。",
              "3. 实际加载 $design-taste-frontend 打磨构图、字阶、密度、材质和动效。与上一步共享决策，已确认结构仅在有依据且范围允许时调整；不要反复覆盖。",
              "4. 实际加载 $impeccable，先看渲染再审：文件:行号—问题—具体改法—严重度；按清单修复后复看。技能或脚本缺失时明确未加载/未执行及影响，不能凭记忆假称调用。",
              "", "## Lovart 与图像工具实际参与", "先检查宿主工具、账户、素材权限及已授权费用。二者分别分配产物；有多账户且目标不明或需新增付费授权时只问必要问题，继续不依赖它的实现。"]
    for record in (sw, ind):
        if record:
            lines += [f"{record['label']} / Lovart：{record['media_brief']['lovart']}", f"{record['label']} / image：{record['media_brief']['image']}"]
    lines += ["以上媒体建议是按交付面筛选的候选用途，不是逐条强制生成。仅宣传页时，把产品信息层级转为能力示意，保留行业真实性边界；仅产品时不新增营销主视觉。按交付面裁剪素材，不重复生成同一主视觉；Lovart负责视觉探索/宣传版式或品牌素材，图像工具负责独立插画/场景/纹理。先生成/编辑→实际查看筛选→保存项目→接入组件→渲染复核。整屏生成图只作参考，文本、导航、表单和数据必须是真组件。",
              "工具不可用或授权待定时交付可执行素材提示词并标记未执行；不能用本地SVG冒称AI生图，也不能只调用工具就声称已接入。",
              "", "## 实现与验收", "补全该流程必要的默认、空、加载、错误、完成与权限状态；实现真实可操作的关键路径。合成数据、模拟任务、模拟后端明确标注，不假称线上提交、真实智能体执行或企业生产验收。",
              "实现范围严格服从surface，行业操作只在产品界面范围内实施；仅宣传页只验收其导航、CTA和适用表单。沿用项目断点；无现状时至少检查桌面和手机。验证键盘、焦点、对比度、触控、溢出和 prefers-reduced-motion。用浏览器实际查看，并操作适用交互；脚本通过不等于视觉通过。",
              "最终提供运行方法、文件、实际加载/检索/审查记录、截图和交互结果，逐项区分已验证、部分完成、未验证与受阻。简要说明方案后持续完成，不在低影响细节反复询问。"]
    prompt = "\n".join(lines) + "\n"
    return {"schema_version": 1, "software": software, "industry": industry, "scope": scope,
            "surface": surface, "tone": tone, "prompt": prompt,
            "project_inspected": False, "generation_executed": False, "ui_quality_verified": False}


def register(commands, emit):
    def catalog(args):
        kinds = ("software", "industry") if args.kind == "all" else (args.kind,)
        emit({"schema_version": 1, "catalogs": {k: [{"id":p["id"], "label":p["label"], "summary":p["summary"]} for p in profiles(k)] for k in kinds}, "coverage_not_market_ranking": True})
        return 0

    def prompt(args):
        result = compose(args.software, args.industry, args.scope, args.surface, args.tone)
        if args.format == "json":
            emit(result)
        else:
            import sys
            sys.stdout.reconfigure(encoding="utf-8")
            print(result["prompt"], end="")
        return 0

    def export(args):
        # Resolve and compose all content before any mutation. mkdir(exist_ok=False)
        # refuses existing directories/files/symlinks, including empty targets.
        destination = Path(args.output).expanduser().absolute()
        records = []
        for kind in ("software", "industry"):
            for p in profiles(kind):
                result = compose(software=p["id"] if kind == "software" else None,
                                 industry=p["id"] if kind == "industry" else None)
                records.append((f"{kind}/{p['id']}.md", result["prompt"]))
        if not destination.parent.is_dir():
            raise ValueError("Export parent must already exist")
        destination.mkdir(exist_ok=False)
        try:
            for name, content in records:
                target = destination / name
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError("Export path must stay inside destination")
                target.parent.mkdir(exist_ok=True)
                target.write_text(content, encoding="utf-8")
            manifest = {"schema_version":1, "version":"2.1.0", "files":[name for name, _ in records], "generation_executed":False}
            (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            (destination / "README.md").write_text("# 专用提示词包\n\nsoftware/ 为软件功能类型，industry/ 为行业项目提示词。复制对应Markdown到支持技能的AI开发工具；也可用 studio.py prompt 组合两者。替换项目输入后执行。已有项目先读取规范和工作树。\n\n这些文件是提示词，不是已运行的界面或素材。外部技能、Lovart和图像工具需在目标工具中分别可用，不能随提示词自动安装。\n", encoding="utf-8")
        except Exception:
            shutil.rmtree(destination)
            raise
        emit({"output":str(destination), "prompt_count":len(records), "generation_executed":False})
        return 0

    p = commands.add_parser("catalog", help="List software and industry coverage, not market ranking")
    p.add_argument("--kind", choices=("all", "software", "industry"), default="all")
    p.set_defaults(run=catalog)
    p = commands.add_parser("prompt", help="Compose project prompt; does not execute skills or generators")
    p.add_argument("--software")
    p.add_argument("--industry")
    p.add_argument("--scope", choices=SCOPES, default="auto")
    p.add_argument("--surface", choices=SURFACES, default="both")
    p.add_argument("--tone", choices=TONES, default="tech-refined")
    p.add_argument("--format", choices=("markdown", "json"), default="markdown")
    p.set_defaults(run=prompt)
    p = commands.add_parser("export-prompts", help="Export 36 standalone prompts into a new directory")
    p.add_argument("--output", required=True)
    p.set_defaults(run=export)
