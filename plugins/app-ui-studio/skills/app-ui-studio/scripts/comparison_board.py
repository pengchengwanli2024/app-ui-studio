"""Portable local screenshot board. No model calls, project edits or quality scores."""
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit


def board_identity(data):
    content = {"context": data["context"], "candidates": data["candidates"]}
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def text_value(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " must be a nonblank string")
    return value


def identifier(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ValueError(name + " must be a safe identifier")
    return value


def build(args, emit, strict_json, evidence_bytes, image_dimensions):
    source = Path(args.manifest).expanduser().resolve(strict=True)
    data = strict_json(source.read_bytes())
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("Unsupported board schema")
    title = text_value(data.get("title"), "title")
    context = data.get("context")
    candidates = data.get("candidates")
    if not isinstance(context, dict) or not context:
        raise ValueError("context must describe shared capture conditions")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("At least two existing candidates are required")
    validated, files, ids, expected = [], {}, set(), None
    for number, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be an object")
        key = identifier(candidate.get("id"), "candidate id")
        if key in ids:
            raise ValueError("Duplicate candidate id")
        ids.add(key)
        item = {"id": key, "label": text_value(candidate.get("label"), "label"), "note": candidate.get("note", ""), "screens": []}
        if not isinstance(item["note"], str):
            raise ValueError("note must be text")
        if "url" in candidate:
            url = urlsplit(text_value(candidate["url"], "url"))
            if url.scheme not in ("http", "https") or not url.netloc or url.username or url.password:
                raise ValueError("url must be HTTP(S), without embedded credentials")
            item["url"] = candidate["url"]
        screens = candidate.get("screens")
        if not isinstance(screens, list) or not screens:
            raise ValueError("candidate needs screenshots")
        dimensions = {}
        for index, screen in enumerate(screens):
            if not isinstance(screen, dict):
                raise ValueError("screen must be an object")
            name = identifier(screen.get("id"), "screen id")
            viewport = screen.get("viewport")
            if (not isinstance(viewport, dict) or any(type(viewport.get(k)) is not int or viewport[k] <= 0 for k in ("width", "height"))):
                raise ValueError("viewport must contain positive integer dimensions")
            size = {k: viewport[k] for k in ("width", "height")}
            raw = evidence_bytes(source.parent, screen.get("artifact"))
            if image_dimensions(raw) != (size["width"], size["height"]):
                raise ValueError("Screenshot dimensions do not match viewport")
            if name in dimensions:
                raise ValueError("Duplicate screen id")
            dimensions[name] = size
            extension = ".png" if raw.startswith(b"\x89PNG") else ".jpg"
            artifact = f"assets/{number}-{index}{extension}"
            files[artifact] = raw
            item["screens"].append({"id": name, "artifact": artifact, "viewport": size, "sha256": hashlib.sha256(raw).hexdigest()})
        if expected is not None and dimensions != expected:
            raise ValueError("Candidates must use the same screen IDs and viewports")
        expected = dimensions
        validated.append(item)
    result = {"schema_version": 1, "title": title, "context": context, "candidates": validated,
              "artifact_contract_valid": True, "visual_quality_verified": False,
              "selection_applied": False, "generation_executed": False,
              "limits": ["Only file headers and declared capture conditions were checked.", "Selection is local feedback, not a project edit or quality verdict."]}
    result["board_id"] = board_identity(result)
    payload = json.dumps(result, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    skill = Path(__file__).resolve().parent.parent
    template = (skill / "assets/comparison-board.html").read_text(encoding="utf-8")
    script = (skill / "scripts/board_feedback.js").read_text(encoding="utf-8")
    page = template.replace("__SCRIPT__", script).replace("__DATA__", payload).replace("<title>设计候选对比</title>", "<title>" + html.escape(title) + "</title>")
    destination = Path(args.output).expanduser().absolute()
    if not destination.parent.is_dir():
        raise ValueError("Output parent must exist")
    destination.mkdir(exist_ok=False)
    try:
        (destination / "assets").mkdir()
        for name, raw in files.items():
            (destination / name).write_bytes(raw)
        (destination / "board.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (destination / "index.html").write_text(page, encoding="utf-8")
    except Exception:
        shutil.rmtree(destination)
        raise
    emit({"output": str(destination), "candidate_count": len(validated),
          **{key: result[key] for key in ("artifact_contract_valid", "visual_quality_verified", "selection_applied", "generation_executed", "limits")}})
    return 0


def register(commands, emit, strict_json, evidence_bytes, image_dimensions):
    parser = commands.add_parser("board", help="Build a portable screenshot board; no design generation or quality scoring")
    parser.add_argument("manifest")
    parser.add_argument("--output", required=True)
    parser.set_defaults(run=lambda args: build(args, emit, strict_json, evidence_bytes, image_dimensions))
