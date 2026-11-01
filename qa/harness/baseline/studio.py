"""Local-only helpers. No network, downloads, hooks, or upstream skill writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
NAMES = ("ui-ux-pro-max", "mobile-app-design", "design-taste-frontend", "impeccable")
STAGES = ("brief", "visuals", "code", "browser", "native_device", "editable_design")
STATUSES = {"verified", "partial", "not_executed", "needs_input"}
TONES = ("calm", "tech-refined", "tech-expressive")
SCOPES = ("auto", "new", "existing", "mixed")
SURFACES = ("product", "marketing", "both")


def design_profile(tone="tech-refined", scope="auto", surface="both"):
    data = json.loads((SKILL / "assets" / "saas-presets.json").read_text(encoding="utf8"))
    selected = dict(data["tones"][tone])
    selected["surfaces"] = {key: selected.pop(key) for key in ("product", "marketing")
                            if surface == "both" or key == surface}
    # Unselected surface text must not imply extra work outside the user's scope.
    selected.pop("product", None)
    selected.pop("marketing", None)
    return {"mode": "saas", "tone": tone, "scope": scope, "surface": surface,
            "project_rule": data["project_rules"][scope], "profile": selected,
            "shared_rules": data["shared_rules"],
            "media_assignments": data["media_assignments"],
            "workflow": data["workflow"], "generation_performed": False,
            "project_inspected": False}


def preset(args):
    emit(design_profile(args.tone, args.scope, args.surface))
    return 0


def emit(value):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(value, ensure_ascii=False, indent=2))


def probe_version(command):
    """Only harmless version probes of known local runtimes; never launch skills."""
    if not shutil.which(command[0]):
        return {"available": False}
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=8, shell=False)
        return {"available": result.returncode == 0,
                "version": (result.stdout or result.stderr).strip()[:180]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "reason": type(exc).__name__}


def doctor(args):
    roots = []
    if os.environ.get("CODEX_HOME"):
        roots.append(Path(os.environ["CODEX_HOME"]) / "skills")
    roots.extend((Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills"))
    roots = list(dict.fromkeys(p.resolve() for p in roots))
    skills = {}
    for name in NAMES:
        candidates = []
        for root in roots:
            entry = root / name / "SKILL.md"
            if entry.is_file():
                candidates.append({"base": str(entry.parent), "entry": str(entry),
                                   "sha256": hashlib.sha256(entry.read_bytes()).hexdigest()})
        skills[name] = {"entry_found": bool(candidates), "candidates": candidates,
                        "host_enabled": "unknown", "runtime_executed": False}
    project = Path(args.project).resolve() if args.project else None
    emit({"local_only": True, "skills": skills,
          "runtime": {"python": sys.version.split()[0], "node": probe_version(["node", "--version"])},
          "project": {"exists": project.is_dir() if project else None,
                      "context_files": [n for n in ("PRODUCT.md", "DESIGN.md", "AGENTS.md")
                                        if project and (project / n).is_file()]},
          "limits": ["File presence is not host activation or workflow acceptance.",
                     "No Impeccable engine, browser, image or design service was called."]})
    return 0


def parse_hex(value):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("Use opaque #RRGGBB colors; composite transparency before checking.")
    return [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def luminance(rgb):
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(args):
    a, b = sorted((luminance(parse_hex(args.foreground)), luminance(parse_hex(args.background))))
    ratio = (b + 0.05) / (a + 0.05)
    emit({"foreground": args.foreground, "background": args.background,
          "ratio": round(ratio, 4), "aa_normal": ratio >= 4.5,
          "aa_large": ratio >= 3, "aaa_normal": ratio >= 7,
          "ui_nontext_threshold": ratio >= 3,
          "limits": "Color pair only; actual rendered colors and applicable exceptions require review."})
    return 0


def init(args):
    target = Path(args.output).expanduser().absolute()
    if target.exists() or target.is_symlink():
        raise ValueError("Output already exists; refusing to overwrite. Choose a new directory.")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive directory creation closes the exists/mkdir race on every platform.
    # On I/O failure, preserve partial artifacts for inspection; never delete user paths.
    target.mkdir()
    delivery_source = "saas-delivery-template.json" if args.mode == "saas" else "delivery-template.json"
    for source, name in (("brief-template.md", "brief.md"),
                         (delivery_source, "delivery.json")):
        with (target / name).open("xb") as output:
            output.write((SKILL / "assets" / source).read_bytes())
    files = ["brief.md", "delivery.json"]
    if args.mode == "saas":
        with (target / "design-profile.json").open("x", encoding="utf8") as output:
            json.dump(design_profile(), output, ensure_ascii=False, indent=2)
        files.append("design-profile.json")
    emit({"created": str(target), "files": files,
          "stages": "not_executed"})
    return 0


def check(args):
    path = Path(args.delivery).resolve()
    root = path.parent
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    errors = []
    if not isinstance(data, dict):
        raise ValueError("Delivery must be a JSON object.")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("schema_version must be 1")
    for key in ("project", "surface"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key} must be a nonempty string")
    stages = data.get("stages")
    if not isinstance(stages, dict):
        raise ValueError("stages must be an object.")
    reported = {}
    for stage in STAGES:
        item = stages.get(stage)
        if not isinstance(item, dict):
            errors.append(f"{stage}: missing stage object")
            continue
        status = item.get("status")
        reported[stage] = status
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{stage}: invalid status")
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{stage}: evidence must be a list")
            continue
        if status == "verified" and not evidence:
            errors.append(f"{stage}: verified requires actual evidence files")
        if not isinstance(item.get("notes"), str):
            errors.append(f"{stage}: notes must be a string")
        for value in evidence:
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{stage}: invalid evidence path")
                continue
            relative = Path(value)
            candidate = (root / relative).resolve()
            if relative.is_absolute() or not candidate.is_relative_to(root):
                errors.append(f"{stage}: evidence must stay inside delivery directory")
            elif not candidate.is_file() or candidate.stat().st_size == 0:
                errors.append(f"{stage}: missing or empty evidence: {value}")
    remaining = data.get("remaining")
    if not isinstance(remaining, list) or any(not isinstance(x, str) for x in remaining):
        errors.append("remaining must be a list of strings")
    mode = data.get("design_mode")
    if mode is not None:
        if not isinstance(mode, dict):
            errors.append("design_mode must be an object")
        else:
            for key, allowed in (("mode", ("saas",)), ("tone", TONES),
                                 ("scope", SCOPES), ("surface", SURFACES)):
                value = mode.get(key)
                if not isinstance(value, str) or value not in allowed:
                    errors.append(f"design_mode.{key}: invalid value")
    creative = {}
    if "requested_creative_providers" in data or "creative_runs" in data:
        requested = data.get("requested_creative_providers")
        valid_requested = (isinstance(requested, list) and
                           all(isinstance(x, str) and x in ("lovart", "image") for x in requested))
        if not valid_requested:
            errors.append("requested_creative_providers must list lovart and/or image")
            requested = []
        elif len(set(requested)) != len(requested):
            errors.append("requested_creative_providers contains duplicates")
        runs = data.get("creative_runs")
        if not isinstance(runs, list):
            errors.append("creative_runs must be a list")
            runs = []
        for item in runs:
            if not isinstance(item, dict):
                errors.append("creative_runs: invalid record")
                continue
            provider = item.get("provider")
            if not isinstance(provider, str) or provider not in ("lovart", "image"):
                errors.append("creative_runs: unsupported provider")
                continue
            if provider in creative:
                errors.append(f"creative_runs: duplicate provider {provider}")
            status = item.get("status")
            creative[provider] = status
            if not isinstance(status, str) or status not in STATUSES:
                errors.append(f"{provider}: invalid status")
            for key in ("purpose", "notes"):
                if not isinstance(item.get(key), str):
                    errors.append(f"{provider}.{key}: must be a string")
            for key in ("output_files", "used_in", "evidence"):
                values = item.get(key)
                if not isinstance(values, list):
                    errors.append(f"{provider}.{key}: must be a list")
                    continue
                if status == "verified" and not values:
                    errors.append(f"{provider}.{key}: verified requires local artifacts, component mapping and evidence")
                for value in values:
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"{provider}.{key}: invalid path")
                        continue
                    relative = Path(value)
                    candidate = (root / relative).resolve()
                    if relative.is_absolute() or not candidate.is_relative_to(root):
                        errors.append(f"{provider}.{key}: path must stay inside delivery directory")
                    elif not candidate.is_file() or candidate.stat().st_size == 0:
                        errors.append(f"{provider}.{key}: missing or empty file: {value}")
        for provider in requested:
            if provider not in creative:
                errors.append(f"{provider}: requested provider has no creative_runs record")
    emit({"artifact_contract_valid": not errors, "errors": errors,
          "reported_stages": reported, "reported_creative_stages": creative,
          "ui_quality_verified": False,
          "limits": "Checks schema and local file presence only; provider execution, image authenticity, component integration, interactions, native devices and editable layers are not verified."})
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("doctor", help="Read-only skill entry and runtime discovery")
    p.add_argument("--project")
    p.set_defaults(run=doctor)
    p = commands.add_parser("contrast", help="Opaque sRGB contrast ratio")
    p.add_argument("foreground")
    p.add_argument("background")
    p.set_defaults(run=contrast)
    p = commands.add_parser("init", help="Copy templates into a new directory; never overwrite")
    p.add_argument("--output", required=True)
    p.add_argument("--mode", choices=("default", "saas"), default="default")
    p.set_defaults(run=init)
    p = commands.add_parser("preset", help="Read a SaaS design profile; never generate images or modify a project")
    p.add_argument("mode", choices=("saas",))
    p.add_argument("--tone", choices=TONES, default="tech-refined")
    p.add_argument("--scope", choices=SCOPES, default="auto")
    p.add_argument("--surface", choices=SURFACES, default="both")
    p.set_defaults(run=preset)
    p = commands.add_parser("check", help="Validate delivery contract and evidence paths, not UI quality")
    p.add_argument("delivery")
    p.set_defaults(run=check)
    args = parser.parse_args()
    try:
        return args.run(args)
    except (OSError, ValueError, TypeError) as exc:
        emit({"error": str(exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
