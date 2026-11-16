"""Portable local screenshot board. No model calls, project edits or quality scores."""
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit


PAGE = r'''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>设计候选对比</title>
<style>
:root{font-family:system-ui,sans-serif;color:#18202b;background:#f3f4f6;line-height:1.5}*{box-sizing:border-box}body{margin:0}main{padding:24px;max-width:1800px;margin:auto}h1{font-size:26px;margin:0 0 8px}h2{font-size:18px;margin:0}p{margin:8px 0}header{margin-bottom:20px}.tools{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:16px 0}button,select,textarea{font:inherit;border:1px solid #697586;border-radius:6px;padding:9px 12px;color:inherit;background:white}button,select{min-height:44px}button{cursor:pointer}button[aria-pressed=true]{background:#163f6b;color:white}button:focus-visible,select:focus-visible,textarea:focus-visible,a:focus-visible{outline:3px solid #216bc4;outline-offset:3px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:20px}.card{background:white;border:1px solid #cbd0d8;border-radius:10px;padding:16px;min-width:0}.card.chosen{border:2px solid #163f6b;padding:15px}.preview{display:block;width:100%;padding:0;border:1px solid #cbd0d8;background:#e9edf2;margin:12px 0;overflow:hidden}.preview img{display:block;width:100%;height:auto;max-height:620px;object-fit:contain}.meta{font-size:13px;color:#465467}.actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap}section.feedback{margin-top:24px;display:grid;gap:8px;max-width:820px}textarea{width:100%;min-height:90px;resize:vertical}dialog{max-width:96vw;max-height:94vh;padding:16px;border:1px solid #697586;border-radius:10px}dialog::backdrop{background:#18202b99}.full{overflow:auto;max-width:90vw;max-height:78vh}.full img{display:block;max-width:none}#status{min-height:24px}@media(max-width:520px){main{padding:16px}h1{font-size:23px}.grid{gap:16px}}
</style>
<main><header><h1 id="title"></h1><p id="context" class="meta"></p><p>截图用于共同观察。页面不会评分、认证截图真实性或自动修改项目。</p></header>
<div class="tools"><label for="viewport">对比视口</label><select id="viewport"></select><span class="meta">点击截图查看原尺寸</span></div>
<div id="grid" class="grid"></div>
<section class="feedback" aria-label="选择与反馈"><label for="notes">喜欢、保留与需要调整的地方</label><textarea id="notes"></textarea><label for="summary">可复制的选择意见</label><textarea id="summary" readonly></textarea><button id="copy" type="button">复制意见</button><p id="status" role="status" aria-live="polite">尚未选择候选</p></section></main>
<dialog id="detail" aria-labelledby="detail-label"><button id="close" type="button">关闭原尺寸预览</button><p id="detail-label"></p><div class="full"><img id="full-image" alt=""></div></dialog>
<script id="board-data" type="application/json">__DATA__</script>
<script>
'use strict';
const data=JSON.parse(document.getElementById('board-data').textContent);
const $=id=>document.getElementById(id);let selected=null;let viewport=data.candidates[0].screens[0].id;
$('title').textContent=data.title;$('context').textContent=JSON.stringify(data.context);
for(const screen of data.candidates[0].screens){const option=document.createElement('option');option.value=screen.id;option.textContent=`${screen.id} · ${screen.viewport.width} × ${screen.viewport.height}`;$('viewport').append(option)}
function updateSummary(){const item=data.candidates.find(c=>c.id===selected);$('summary').value=item?`选择方案 ${item.label}（${item.id}）；视口：${viewport}。\n意见：${$('notes').value||'待补充'}`:''}
function render(){const grid=$('grid');grid.replaceChildren();for(const item of data.candidates){const screen=item.screens.find(s=>s.id===viewport);const card=document.createElement('article');card.className='card'+(item.id===selected?' chosen':'');const title=document.createElement('h2');title.textContent=item.label;const note=document.createElement('p');note.textContent=item.note||'';const preview=document.createElement('button');preview.type='button';preview.className='preview';preview.setAttribute('aria-label',`原尺寸查看 ${item.label}`);const img=document.createElement('img');img.src=screen.artifact;img.alt=`${item.label}，${viewport}截图`;preview.append(img);preview.onclick=()=>{$('full-image').src=screen.artifact;$('full-image').alt=img.alt;$('detail-label').textContent=`${item.label} · ${screen.viewport.width} × ${screen.viewport.height}`;$('detail').showModal()};const actions=document.createElement('div');actions.className='actions';const choose=document.createElement('button');choose.type='button';choose.textContent=item.id===selected?'已选择':'选择此方案';choose.setAttribute('aria-pressed',String(item.id===selected));choose.onclick=()=>{selected=item.id;for(const c of grid.children){const active=c.dataset.id===selected;c.classList.toggle('chosen',active);const b=c.querySelector('.choose');b.textContent=active?'已选择':'选择此方案';b.setAttribute('aria-pressed',String(active))}$('status').textContent=`已选择 ${item.label}；尚未应用到项目`;updateSummary()};choose.className='choose';actions.append(choose);if(item.url){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='打开实际页面';actions.append(link)}card.dataset.id=item.id;card.append(title,note,preview,actions);grid.append(card)}updateSummary()}
$('viewport').onchange=()=>{viewport=$('viewport').value;render()};$('notes').oninput=updateSummary;
$('copy').onclick=async()=>{if(!selected){$('status').textContent='请先选择候选';return}try{await navigator.clipboard.writeText($('summary').value);$('status').textContent='已复制选择意见；尚未应用到项目'}catch{$('summary').focus();$('summary').select();$('status').textContent='自动复制不可用，请复制已选中的意见'}};
$('close').onclick=()=>$('detail').close();render();
</script></html>'''


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
    payload = json.dumps(result, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    page = PAGE.replace("__DATA__", payload).replace("<title>设计候选对比</title>", "<title>" + html.escape(title) + "</title>")
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
