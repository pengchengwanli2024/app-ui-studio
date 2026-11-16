"""Scoped design prompts. Does not inspect projects, write files or execute tools."""
import sys

from prompt_library import SCOPES, SURFACES, TONES as LEGACY_TONES, resolve
from oil_ecosystem import capability_profiles

TONES = ("auto", *LEGACY_TONES)


TASKS = {
    "brief": ("方案与素材简报", "只交方案、提示词或素材计划，不改产品文件、不生成素材、不进入实现。"),
    "design": ("设计与实现", "在本次范围内确定对象、结构与一个推荐方向；已有方向继续深化。"),
    "polish": ("存量精修", "在现有结构与视觉语言内修层级、密度和一致性；改变范围须有用户依据。"),
    "extend": ("新增功能或调整流程", "补齐新任务的入口、数据、状态、完成与恢复；沿用现有品牌、tokens与组件。"),
    "reconstruct": ("原型或截图还原", "先列参考元素到项目变量、组件和交互的映射；用真实组件还原，保留工程外壳。"),
    "audit": ("只读评审", "只调查并交付有位置、证据、影响和具体建议的问题；不修改项目或进入修正循环。"),
}
DOMAINS = {
    "auto": "读取实际页面任务后逐页判断领域，软件类型和行业不足以决定构图；不默认生成仪表盘。",
    "workspace": "工作区：按对象处理选择列表/表格、队列+详情、分组表单或编辑画布；让对象、判断依据与动作相邻，保持筛选、选择、滚动和焦点。",
    "content": "内容浏览：先确定对象的识别属性与单项表现，再铺列表、网格或索引；首屏以可判断的内容为主，筛选贴近内容，从详情返回原位置。",
    "persuasion": "说服页：先按受众与内容选择整体构图，再安排价值、真实证据和有效CTA；方向贯穿整页，不编造背书或以宣传图代替产品。",
    "play": "操作体验：先确定操控规则、反馈时机、暂停/恢复和输入方式；看图与实际操控分开验收，尊重低动效设置。",
}
PLATFORMS = ("auto", "desktop", "mobile", "cross-platform", "native-ios", "native-android", "mini-program")
VIEWPORTS = {
    "auto": [], "desktop": [{"width": 1440, "height": 900}],
    "mobile": [{"width": 390, "height": 844}],
    "cross-platform": [{"width": 1440, "height": 900}, {"width": 390, "height": 844}],
    "native-ios": [], "native-android": [], "mini-program": [],
}
SPECIALTIES = {
    "component": {
        "reference": "references/component-craft.md",
        "steps": ["先定义组件回答的问题、主操作、实际承载尺寸和必要状态；工作区沿用功能表达，不强制实物图或品牌演出。",
                  "把触发器、当前值、选项行、选中/焦点标识与展开反馈分别做小型试样，选定后只深化一种；检查原尺寸和页面上下文。"],
        "checks": ["核对长值、空值、禁用、展开/收起、键盘取消和焦点返回；实际主操作与共享使用处另验，静态图不证明手感。"],
    },
    "media": {
        "reference": "references/media-tools.md",
        "steps": ["每项素材先写用途与信息目标，再选复用、裁切、编辑、补拍、生成或代码表达；不为凑流程调用提供方。",
                  "成套锁定主体身份、比例、镜头、光向、材质、色板与文字安全区；先在真实版式检查代表素材，再延展其他画面。"],
        "checks": ["检查真实产品身份与来源、窄屏裁切、alpha边缘、加载和组件落点；无生成能力交可执行简报，生成阶段未执行。"],
    },
    "motion": {
        "reference": "references/motion-scroll.md",
        "steps": ["按触发→受影响对象→起止状态→打断→低动效列动作；按压立即反馈，成功与完成演出等待真实回执。",
                  "过渡从当前值连续衔接，业务不等待动画结束；沿用项目时长/缓动，离屏、隐藏和卸载停止并清理。"],
        "checks": ["正常速度、反向、快速重复、慢响应/超时及减少动态效果分别操作；静态截图不证明时序或帧率。"],
    },
    "scroll": {
        "reference": "references/motion-scroll.md",
        "steps": ["仅说服/品牌表面采用滚动叙事，工作区与阅读页保留原生滚动；先完成静态步骤，再定义段落→进度区间→关键画面→稳定文字→退出。",
                  "区分位置驱动与一次触发；反向、刷新到中段和锚点跳入须得到正确画面。按手机空间缩短或取消固定区间。"],
        "checks": ["减少动态效果、脚本或媒体失败时保留同等静态信息；检查跳过、CTA、正反滚动、加载和手机裁切，不以小点移动冒充完整叙事。"],
    },
    "explore": {
        "reference": "references/exploration.md",
        "steps": ["本次明确比较候选：锁定任务、事实、品牌与素材质量，按结构、比例与阅读顺序表达差别，不只换色。",
                  "只做足以选择的首屏或关键片段，同视口/状态并排，给收益、代价与推荐；选择前不铺全站。用户已授权代选时自主选定后只深化所选。"],
        "checks": ["逐候选核对产品识别、主操作、文字可读与窄屏裁切；board仅展示截图，compare仅查证据契约，都不代替视觉判断。"],
    },
    "iterate": {
        "reference": "references/iteration.md",
        "steps": ["先列用户原话→画面证据→可检验假设→最小验证片段→修改位置→已确认项影响；没被提到的内容不自动算认可。",
                  "沿用已定方向和品牌，只改有依据的部分；同视口/数据/状态保留前后对照，共享修改复看受影响页面。"],
        "checks": ["同一区域反复不满意、意见相反或明显要求另一方向时停止猜细节，指出方向假设与锁定项冲突；未经授权不重塑，无新证据不循环。"],
    },
}
for _profile in capability_profiles():
    if _profile['id'] in SPECIALTIES:
        raise ValueError('Duplicate specialty across capability sources')
    SPECIALTIES[_profile['id']] = _profile


def build(task=None, domain="auto", scope="auto", surface="product",
          platform="auto", tone="auto", software=None, industry=None, focus=None, directions=None):
    if focus is not None and focus not in SPECIALTIES:
        raise ValueError("Unknown specialty")
    guide = SPECIALTIES.get(focus, {})
    task = guide.get('default_task', 'design') if task is None else task
    if 'allowed_tasks' in guide and task not in guide['allowed_tasks']:
        raise ValueError(f"{focus} supports only: " + ', '.join(guide['allowed_tasks']))
    focused = 'sources' in guide
    artifact = focused and focus not in ('frontend', 'mockup', 'native-ios', 'node-editor', 'art-direction', 'media-runtime')
    for value, choices, label in ((task, TASKS, "task"), (domain, DOMAINS, "domain"),
                                  (scope, SCOPES, "scope"), (surface, SURFACES, "surface"),
                                  (platform, PLATFORMS, "platform"), (tone, TONES, "tone")):
        if value not in choices:
            raise ValueError(f"Unknown {label}: {value}")
    if surface == "marketing" and domain not in ("auto", "persuasion"):
        raise ValueError("marketing surface requires domain=auto or persuasion")
    domains = ["persuasion"] if surface == "marketing" else [domain]
    if surface == "both" and "persuasion" not in domains:
        domains.append("persuasion")
    if directions is not None and (focus != "explore" or type(directions) is not int or directions < 2):
        raise ValueError("--directions requires --focus explore and at least 2 candidates")
    if task != "audit" and focus == "scroll" and "persuasion" not in domains and "auto" not in domains:
        raise ValueError("Scroll narrative requires a persuasion surface")
    profiles = [(kind, resolve(kind, identifier)) for kind, identifier in
                (("software", software), ("industry", industry)) if identifier is not None]
    read_only = task == "audit"
    plan_only = task == "brief"
    preserve = ["brand", "existing-work", "unrequested-behavior"]
    if task in ("polish", "extend") or (task == "design" and scope in ("existing", "mixed")):
        preserve.append("visual-system")
    if task == "polish":
        preserve.append("workflow")
    if focus == "iterate":
        preserve.append("approved-decisions")
    review_mode = "evidence-only" if read_only else "plan-review" if plan_only else (
        "baseline-comparison" if task in ("polish", "extend", "reconstruct")
        or scope in ("existing", "mixed") else "new-direction")
    lines = ["# APP UI Studio 范围与领域提示词", "", "## 本次任务",
             "用户要求：[填写原始请求、输入与可操作的成功条件；用户要求优先于本模板]",
             f"任务：{TASKS[task][0]}；scope={scope}；surface={surface}；platform={platform}；tone={tone}",
             TASKS[task][1],
             "说明跟随用户语言，界面文案跟随产品语言。先读相关工作树、路由、组件、tokens与设计规范；Confirmed / Observed / Assumed / Unknown分开。",
             "只读相关范围，不因没有DESIGN.md就当成新项目；不创建相互竞争的规范。"]
    if artifact:
        lines += ["", "## 交付对象", "以用户要求的文案、素材、分析或交接文件为范围；页面领域参数仅在需要实际页面落点时使用，不据此增加页面或功能。"]
    else:
        lines += ["", "## 页面领域"]
        lines.extend(DOMAINS[item] for item in domains)
        lines.append("逐页按实际任务应用骨架；跨领域共享语义品牌，不共用不合适的密度、标题比例或动效。")
    if surface == "marketing" and not artifact:
        lines.append("只交付宣传页的范围，行业信息约束文案与示意，不实施后台工作流。")
    elif surface == "both" and not artifact:
        lines.append("产品与宣传页分别定义任务和代表页；共享品牌与真实已完成的产品屏幕。")
    for kind, record in profiles:
        keys = ("ux_rules", "boundaries") if kind == "industry" else ("ux_rules",)
        lines += ["", f"## {'软件' if kind == 'software' else '行业'}参考：{record['label']}", record["summary"],
                  "以下是待裁剪候选，仅采用与本次用户主任务相关的条目；不据此增加模块。"]
        lines.extend("；".join(record[key]) for key in keys)
    lines += ["", "## 取证与能力边界",
              "只使用实际可用且已授权的技能、浏览器与素材工具；外部设计技能和生图均非默认前置，不因缺失而停止独立工作。",
              "使用同版本、同视口、同数据与状态的证据。先看整体构图，再看原尺寸的文字、控件、长内容、焦点与浮层。"]
    if platform == "auto":
        lines.append("读取项目后确定实际目标端与视口，不为单端任务补造另一个设备外壳。")
    elif platform.startswith("native-"):
        lines.append("使用实际原生设备或模拟器及平台单位；Web像素宽度不证明原生触控、安全区与键盘验收。")
    elif platform == "mini-program":
        lines.append("核对小程序工程的逻辑视口、rpx基准、平台组件与实际渲染；分别记录H5预览、开发者工具和真机，不把图片像素或浏览器宽度当成平台验收。")
    else:
        sizes = "、".join(f"{v['width']}×{v['height']}" for v in VIEWPORTS[platform])
        lines.append(f"无项目断点依据时，以{sizes}作为起始视口，按实际内容补查长文本、缩放和键盘遮挡。")
    if read_only:
        lines += ["", "## 只读交付",
                  "按影响排序报告位置、实际观察、证据与建议；截图不能证明操作可达、保存成功或真实用户理解。只有静态证据时写明未操作验证。",
                  "独立评审须有实际独立执行者；没有则明确自检，不编造独立回执、评分或通过结论。交付分析后停止，不修改文件。"]
    elif plan_only:
        lines += ["", "## 方案交付",
                  ("按本次专项交付可执行的说明、分析提纲或制作简报：已知事实、所需输入、锁定项、拟议步骤与验证办法；仅使用适用部分。" if focused else
                   "交付可执行的方案/素材简报：用途与受众、现有输入、锁定项、构图与比例、素材来源选择、必要提示词、预计组件落点与验收办法。"),
                  "已观察的素材与拟议画面分别标注；缺图、无生成服务或未制作版式不伪装为已完成。只构思时不生成素材、不写产品代码、不延伸为整站制作。"]
    elif focused:
        lines += ["", "## 专项实施与交付",
                  "只完成本次专项要求的对象与文件，沿用现有品牌、事实和已确认方向；不因选了专项就铺开整站或额外格式。",
                  "先做可验证的代表片段，按专项检查实际结果后延展必要范围；代码、文案、素材与运行回执分别核对。",
                  "外部工具、生成、安装、上传和发布各按实际授权与可用能力执行；缺能力时交可执行简报并标记未执行，不编造成功。",
                  "交付真实文件/入口、已执行验证与剩余缺口；共享修改复看受影响使用处，普通任务最终简述即可。"]
    else:
        lines += ["", "## 实施顺序",
                  "默认深化一个推荐方向，只有明确请求比较时才出多个。已定方向与品牌继续沿用；tone只作为未锁定部分的提案，不强制科技特效。",
                  "多屏先列页面→领域→入口/完成/返回→代表页→状态，锁定全局导航；小组件与局部修复无需整套地图。",
                  "先实现代表页和关键状态，实际检查后再复用共享tokens、组件与导航分批铺开；共享修改复看其他使用处。",
                  "实现定位对象→查看依据→执行→结果反馈。批量、外部写入和重试区分处理中/成功/失败/未知，按回执与幂等契约恢复；保存后刷新读回。",
                  "素材只承担真实图片的职责；文字、输入、导航与数据用组件实现。原型还原先做复用映射，同视口逐项核对。",
                  "", "## 分层验收与交付",
                  "视觉检查看构图、可读性与一致性；操作验证走一条主要路径及关键边界/失败恢复，结果分别记录。",
                  "若有独立评审者，视觉审查提供截图与约束；探索UX只给入口、目标设备与必要测试资料，让其自行理解路径。功能回归另按业务契约验证。无独立能力则标自检。",
                  "优先修业务/交互、结构/布局，再修组件一致性和装饰；修后只重验受影响范围，无新证据或审美来回横跳时停止。",
                  "交付真实代码入口、运行方式、实际证据与剩余项，分别标verified / partial / not_executed / needs_input。普通修改最终简述即可，既有文档原地更新。",
                  "用户已授权实施或说你定/直接做时持续完成；仅当缺失信息实质影响业务、权限或高代价操作时询问。"]
    specialty = None
    if focus:
        guide = SPECIALTIES[focus]
        specialty = {"reference": guide["reference"],
                     "mode": "functional" if focus == "component" and domain == "workspace" else "contextual",
                     "applies_to": ["persuasion"] if focus == "scroll" and not read_only else domains}
        if 'sources' in guide:
            specialty['sources'] = guide['sources']
        lines += ["", f"## 专项：{focus}"]
        if read_only:
            lines.append("本次只读：以下仅作为观察维度，不制作候选、不修改文件或执行修正。")
            lines.extend(guide.get('audit_steps', []))
            lines.extend(guide["checks"])
        else:
            if plan_only:
                lines.append("本次只交方案：下列动作用于描述拟议步骤与验收安排，不实际制作、生成或改动项目。")
            lines.extend(guide["steps"] + guide["checks"])
        lines.append("详细方法：" + guide["reference"] + "（有插件目录时按需读取；专项不扩大原任务授权）。")
    count = 0 if read_only else ((directions or 3) if focus == "explore" else 1)
    if focus == "explore" and not read_only:
        lines.append(f"本轮候选数量：{count}；用户另有明确数量或锁定项时以用户为准。")
    result = {"schema_version": 1, "workflow_version": "2.5.0", "task": task, "domains": domains,
            "scope": scope, "surface": surface, "platform": platform, "tone": tone,
            "software": software, "industry": industry, "preserve": preserve,
            "execution": {"project_writes": not (read_only or plan_only), "implementation": not (read_only or plan_only),
                          "external_skills_required": False, "media_required": False},
            "review_mode": review_mode, "suggested_viewports": VIEWPORTS[platform],
            "recommended_directions": count, "independent_review_executed": False,
            "prompt": "\n".join(lines) + "\n", "project_inspected": False,
            "generation_executed": False, "ui_quality_verified": False}
    if focus:
        result.update(focus=focus, specialty=specialty)
    if plan_only:
        result["deliverable"] = "brief"
    return result


def run(args, emit):
    result = build(**{key: getattr(args, key) for key in
                      ("task", "domain", "scope", "surface", "platform", "tone", "software", "industry", "focus", "directions")})
    if args.format == "json":
        emit(result)
    else:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        print(result["prompt"], end="")
    return 0


def register(commands, emit):
    parser = commands.add_parser("workflow", help="Compose scoped design guidance; no project or tool execution")
    for name, choices, default in (("task", tuple(TASKS), None), ("domain", tuple(DOMAINS), "auto"),
                                   ("scope", SCOPES, "auto"), ("surface", SURFACES, "product"),
                                   ("platform", PLATFORMS, "auto"), ("tone", TONES, "auto")):
        parser.add_argument("--" + name, choices=choices, default=default)
    parser.add_argument("--software")
    parser.add_argument("--industry")
    parser.add_argument("--focus", choices=tuple(SPECIALTIES))
    parser.add_argument("--directions", type=int)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.set_defaults(run=lambda args: run(args, emit))
