#!/usr/bin/env python3
"""Stdlib-only repository preflight for the APP UI Studio 2.1.0 examples.

Run from the repository root with:
    python3 scripts/verify_project.py

This checks file identity, local references, capture comparability, and public
text/binary strings. It does not launch a browser or validate visual quality.
"""

from __future__ import annotations

import fnmatch
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "app-ui-studio"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "app-ui-studio"
RELEASE_VERSION = "2.1.0"


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.passes: list[str] = []
        self.notes: list[str] = []

    def ok(self, message: str) -> None:
        self.passes.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def finish(self) -> int:
        print("APP UI Studio project preflight")
        for message in self.passes:
            print(f"PASS  {message}")
        for message in self.notes:
            print(f"NOTE  {message}")
        for message in self.errors:
            print(f"FAIL  {message}")
        print(f"Summary: {len(self.passes)} passed, {len(self.notes)} noted, {len(self.errors)} failed")
        return 1 if self.errors else 0


def load_json(path: Path, label: str, report: Report) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.fail(f"{label}: missing file {relative(path)}")
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report.fail(f"{label}: cannot read valid JSON at {relative(path)} ({type(exc).__name__})")
        return None
    if not isinstance(value, dict):
        report.fail(f"{label}: expected a JSON object at {relative(path)}")
        return None
    return value


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_project_file(base: Path, name: str) -> Path | None:
    candidate = (base / name).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        return None
    return candidate


def check_frozen_v11(report: Report) -> None:
    version_root = ROOT / "examples" / "qike" / "v1.1.0"
    frozen = load_json(ROOT / "evidence" / "v1.1.0" / "source-hashes.json",
                       "v1.1 frozen source manifest", report)
    if frozen is None:
        return
    if not frozen:
        report.fail("v1.1 frozen source manifest is empty")
        return
    mismatches: list[str] = []
    for name, expected in sorted(frozen.items()):
        if not isinstance(name, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            mismatches.append("manifest contains an invalid path or SHA-256 value")
            continue
        target = safe_project_file(version_root, name)
        if target is None:
            mismatches.append(f"unsafe frozen path {name}")
        elif not target.is_file():
            mismatches.append(f"missing frozen file {name}")
        elif sha256(target).lower() != expected.lower():
            mismatches.append(f"SHA-256 changed for {name}")
    if mismatches:
        for item in mismatches:
            report.fail(f"v1.1 freeze: {item}")
    else:
        report.ok(f"v1.1 frozen source hashes match ({len(frozen)} files)")


def check_unchanged_app_and_mascot(report: Report) -> None:
    base = ROOT / "examples" / "qike" / "v1.1.0"
    candidate = ROOT / "examples" / "qike" / "v1.2.0"
    for name in ("app.js", "assets/sprout.png"):
        left, right = base / name, candidate / name
        if not left.is_file() or not right.is_file():
            report.fail(f"cross-version invariant: missing {name} in v1.1.0 or v1.2.0")
        elif left.read_bytes() != right.read_bytes():
            report.fail(f"cross-version invariant: {name} differs between v1.1.0 and v1.2.0")
        else:
            report.ok(f"cross-version invariant: {name} is byte-identical")


def manifest_interface(data: dict, path: Path, report: Report) -> dict | None:
    if path.name == "plugin.json" and path.parent.name == "app-ui-studio":
        try:
            interface = data["extensions"]["com.openai"]["interface"]
        except (KeyError, TypeError):
            report.fail(f"manifest {relative(path)} lacks extensions.com.openai.interface")
            return None
    else:
        interface = data.get("interface")
    if not isinstance(interface, dict):
        report.fail(f"manifest {relative(path)} lacks an interface object")
        return None
    return interface


def check_manifest_pair(report: Report) -> None:
    root_path = PLUGIN_ROOT / "plugin.json"
    codex_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    root_manifest = load_json(root_path, "plugin manifest", report)
    codex_manifest = load_json(codex_path, "Codex plugin manifest", report)
    if root_manifest is None or codex_manifest is None:
        return
    for label, data, path in (("plugin", root_manifest, root_path), ("Codex plugin", codex_manifest, codex_path)):
        if data.get("name") != "app-ui-studio":
            report.fail(f"{label} manifest {relative(path)} has unexpected name")
        if data.get("version") != RELEASE_VERSION:
            report.fail(f"{label} manifest {relative(path)} must declare version {RELEASE_VERSION}")
    root_interface = manifest_interface(root_manifest, root_path, report)
    codex_interface = manifest_interface(codex_manifest, codex_path, report)
    if root_interface is not None and codex_interface is not None:
        if root_interface != codex_interface:
            report.fail("root and .codex-plugin display/interface configuration differs")
        else:
            report.ok("root and .codex-plugin display/interface configuration matches")
    if (root_manifest.get("name") == codex_manifest.get("name") == "app-ui-studio"
            and root_manifest.get("version") == codex_manifest.get("version") == RELEASE_VERSION):
        report.ok(f"both plugin manifests identify app-ui-studio version {RELEASE_VERSION}")

    for manifest, interface, label in ((root_manifest, root_interface, "root"),
                                       (codex_manifest, codex_interface, ".codex-plugin")):
        if interface is not None:
            for key in ("composerIcon", "logo"):
                value = interface.get(key)
                if isinstance(value, str) and value.strip():
                    check_manifest_resource(PLUGIN_ROOT, value, f"{label} manifest {key}", report)
                else:
                    report.fail(f"{label} manifest is missing {key}")
        skills = manifest.get("skills")
        if isinstance(skills, str):
            check_manifest_resource(PLUGIN_ROOT, skills, f"{label} manifest skills", report)


def check_manifest_resource(base: Path, value: str, label: str, report: Report) -> None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        report.fail(f"{label}: expected a packaged local path, found a URL")
        return
    target = (base / unquote(parsed.path)).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        report.fail(f"{label}: path escapes plugin package")
        return
    if target.exists():
        report.ok(f"{label} resolves to {relative(target)}")
    else:
        report.fail(f"{label}: missing packaged resource {value}")


MD_INLINE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)")
MD_REFERENCE = re.compile(r"(?m)^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")


def local_destination(value: str) -> str | None:
    value = value.strip().strip("<>")
    if not value or value.startswith("#"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    return path


def check_markdown_references(report: Report) -> None:
    candidates = [SKILL_ROOT / "SKILL.md"]
    assets = SKILL_ROOT / "assets"
    if assets.is_dir():
        candidates.extend(path for path in assets.rglob("*") if path.is_file() and path.suffix.lower() == ".md")
    references = SKILL_ROOT / "references"
    if references.is_dir():
        candidates.extend(path for path in references.rglob("*")
                          if path.is_file() and path.suffix.lower() == ".md")
    checked = 0
    failures = 0
    for source in sorted(set(candidates)):
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            report.fail(f"Markdown reference scan cannot read {relative(source)} ({type(exc).__name__})")
            failures += 1
            continue
        destinations: list[str] = []
        destinations.extend(match.group(1) for match in MD_INLINE.finditer(text))
        destinations.extend(a or b for a, b in MD_REFERENCE.findall(text))
        for value in destinations:
            path_text = local_destination(value)
            if path_text is None:
                continue
            checked += 1
            path = Path(path_text)
            if path.is_absolute():
                report.fail(f"local Markdown reference is absolute at {relative(source)}")
                failures += 1
                continue
            target = (source.parent / path).resolve()
            try:
                target.relative_to(PLUGIN_ROOT.resolve())
            except ValueError:
                report.fail(f"local Markdown reference escapes plugin package at {relative(source)}")
                failures += 1
                continue
            if not target.exists():
                report.fail(f"broken local Markdown reference at {relative(source)}: {path_text}")
                failures += 1
    if not failures:
        report.ok(f"plugin SKILL/assets Markdown references resolve ({checked} local references)")


class HTMLResources(HTMLParser):
    TAG_ATTRIBUTES = {
        "img": ("src", "srcset"),
        "link": ("href",),
        "script": ("src",),
        "iframe": ("src",),
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.resources: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(tag, attrs)

    def _collect(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        allowed = self.TAG_ATTRIBUTES.get(tag.lower(), ())
        for key, value in attrs:
            if value is None or key.lower() not in allowed:
                continue
            if key.lower() == "srcset":
                for candidate in value.split(","):
                    url = candidate.strip().split()
                    if url:
                        self.resources.append((tag, url[0]))
            else:
                self.resources.append((tag, value.strip()))


def web_root_for(path: Path) -> Path:
    for parent in path.parents:
        if re.fullmatch(r"v\d+\.\d+\.\d+", parent.name):
            return parent
    return ROOT


def check_html_resources(report: Report) -> None:
    missing: list[str] = []
    total = 0
    html_files = sorted((ROOT / "examples").rglob("*.html"))
    for html_file in html_files:
        try:
            parser = HTMLResources()
            parser.feed(html_file.read_text(encoding="utf-8"))
            parser.close()
        except (OSError, UnicodeError, ValueError) as exc:
            missing.append(f"{relative(html_file)}: cannot parse HTML ({type(exc).__name__})")
            continue
        web_root = web_root_for(html_file)
        for tag, raw in parser.resources:
            if not raw or raw.startswith("#"):
                continue
            parsed = urlsplit(raw)
            if parsed.scheme and parsed.scheme.lower() != "file":
                continue
            if parsed.netloc and parsed.scheme.lower() != "file":
                continue
            raw_path = unquote(parsed.path)
            if not raw_path:
                continue
            total += 1
            if parsed.scheme.lower() == "file":
                target = Path(raw_path).resolve()
            else:
                candidate = Path(raw_path)
                target = ((web_root / candidate.relative_to("/")) if candidate.is_absolute()
                          else html_file.parent / candidate).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                missing.append(f"{relative(html_file)}: {tag} local resource escapes project")
                continue
            if not target.is_file():
                missing.append(f"{relative(html_file)}: missing {tag} resource {raw_path}")
    if missing:
        for item in missing:
            report.fail(f"HTML resource: {item}")
    elif html_files:
        report.ok(f"HTML img/link/script/iframe local resources exist ({total} checked across {len(html_files)} files; #anchors ignored)")
    else:
        report.note("no example HTML files found; local HTML resource check skipped")


def check_capture_comparison(report: Report, left="v1.1.0", right="v1.2.0", output="comparison.json") -> None:
    baseline = ROOT / "examples" / "qike" / left / "capture.json"
    candidate = ROOT / "examples" / "qike" / right / "capture.json"
    present = (baseline.is_file(), candidate.is_file())
    if not any(present):
        report.fail("both capture.json files are absent; release comparison evidence is required")
        return
    if not all(present):
        report.fail(f"capture comparison requires both {left}/capture.json and {right}/capture.json")
        return
    studio = PLUGIN_ROOT / "skills" / "app-ui-studio" / "scripts" / "studio.py"
    if not studio.is_file():
        report.fail(f"capture comparison: missing {relative(studio)}")
        return
    command = [sys.executable, str(studio), "compare", str(baseline), str(candidate)]
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    except OSError as exc:
        report.fail(f"studio.py compare could not run ({type(exc).__name__})")
        return
    try:
        generated = json.loads(result.stdout)
    except json.JSONDecodeError:
        report.fail(f"studio.py compare returned non-JSON output (exit {result.returncode})")
        return
    if result.returncode != 0:
        report.fail(f"studio.py compare exited {result.returncode}; comparable is not established")
    if generated.get("comparison_contract_valid") is not True or generated.get("comparable") is not True:
        report.fail("studio.py compare did not report a valid comparable capture set")
    if generated.get("visual_quality_verified") is not False:
        report.fail("studio.py compare must preserve visual_quality_verified=false")
    committed_path = ROOT / "evidence" / output
    committed = load_json(committed_path, "comparison evidence", report)
    if committed is not None:
        if committed.get("comparable") is not True or committed.get("visual_quality_verified") is not False:
            report.fail("evidence/comparison.json must state comparable=true and visual_quality_verified=false")
        if committed != generated:
            report.fail("evidence/comparison.json does not match current studio.py compare output")
    if result.returncode == 0 and generated.get("comparable") is True and generated.get("visual_quality_verified") is False and committed == generated:
        report.ok(f"studio.py compare {left}/{right} matches evidence/{output} (comparable=true; visual quality unverified)")


LOCAL_PATH_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9_.-])/(?:Users|home)/[^/\\\s\"'<>]+(?:/|$)"),
    re.compile(r"(?i)(?<![A-Za-z0-9])(?:[A-Z]:)?\\Users\\[^\\\s\"'<>]+(?:\\|$)"),
]
PRIVATE_ID_PATTERNS = [
    re.compile(r"(?i)\blink_[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b(?:link[_-]?id|project[_-]?id|task[_-]?id|artifact[_-]?id)\b\s*[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_-]{8,}"),
]
SIGNED_URL_PATTERNS = [
    re.compile(r"(?i)[?&](?:x-amz-signature|x-goog-signature|signature|sig|access_token|auth_token|token)=[^&\s\"']{8,}"),
    re.compile(r"(?i)\b(?:X-Amz-Credential|AWSAccessKeyId)=[^&\s\"']{8,}"),
]
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-(?:ant-|proj-|live-|svc-)?[A-Za-z0-9_-]{32,}\b"),
    re.compile(r"\b(?:xox[baprs])-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"(?i)\b(?:openai[_-]?api[_-]?key|api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|auth[_-]?token|password|passwd|secret|token)\b\s*[:=]\s*[\"']?([A-Za-z0-9._~+/=-]{16,})"),
]


def gitignore_rules(root: Path) -> tuple[set[str], list[str]]:
    directories = {".git"}
    file_patterns: list[str] = []
    ignore_file = root / ".gitignore"
    if not ignore_file.is_file():
        return directories, file_patterns
    try:
        lines = ignore_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return directories, file_patterns
    for raw in lines:
        pattern = raw.strip()
        if not pattern or pattern.startswith("#") or pattern.startswith("!"):
            continue
        if pattern.endswith("/") and "/" not in pattern[:-1]:
            directories.add(pattern[:-1])
        else:
            file_patterns.append(pattern)
    return directories, file_patterns


def is_ignored_file(path: Path, root: Path, patterns: list[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    for pattern in patterns:
        normalized = pattern.lstrip("/")
        if fnmatch.fnmatchcase(path.name, normalized) or fnmatch.fnmatchcase(rel, normalized):
            return True
    return False


def public_files(report: Report) -> tuple[list[Path], list[str], int]:
    ignored_dirs, ignored_file_patterns = gitignore_rules(ROOT)
    files: list[Path] = []
    ignored: list[str] = []
    symlinks = 0
    for current, dirnames, filenames in os.walk(ROOT, topdown=True, followlinks=False):
        directory = Path(current)
        keep: list[str] = []
        for name in dirnames:
            child = directory / name
            if name in ignored_dirs:
                ignored.append(relative(child) + "/")
            elif child.is_symlink():
                report.fail(f"public scan: symlink directory is not followed: {relative(child)}")
                symlinks += 1
            else:
                keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            path = directory / name
            if is_ignored_file(path, ROOT, ignored_file_patterns):
                ignored.append(relative(path))
            elif path.is_symlink():
                report.fail(f"public scan: symlink file is not followed: {relative(path)}")
                symlinks += 1
            elif path.is_file():
                files.append(path)
    return sorted(files), sorted(ignored), symlinks


def report_public_safety(report: Report) -> None:
    files, ignored, symlinks = public_files(report)
    findings = 0
    text_files = 0
    binary_files = 0
    for path in files:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            report.fail(f"public scan cannot read {relative(path)} ({type(exc).__name__})")
            continue
        try:
            text = raw.decode("utf-8")
            is_text = b"\x00" not in raw
        except UnicodeDecodeError:
            text = ""
            is_text = False
        if is_text:
            text_files += 1
            for line_number, line in enumerate(text.splitlines(), 1):
                groups = (
                    ("local username absolute path", LOCAL_PATH_PATTERNS),
                    ("private provider identifier", PRIVATE_ID_PATTERNS),
                    ("signed URL", SIGNED_URL_PATTERNS),
                    ("secret pattern", SECRET_PATTERNS),
                )
                for category, patterns in groups:
                    if any(pattern.search(line) for pattern in patterns):
                        report.fail(f"public safety: {category} at {relative(path)}:{line_number}")
                        findings += 1
        else:
            binary_files += 1
            # Search raw bytes for ASCII credential/path markers in metadata too.
            groups_b = (
                ("local username absolute path", [re.compile(p.pattern.encode("ascii"), p.flags & ~re.UNICODE) for p in LOCAL_PATH_PATTERNS]),
                ("private provider identifier", [re.compile(p.pattern.encode("ascii"), p.flags & ~re.UNICODE) for p in PRIVATE_ID_PATTERNS]),
                ("signed URL", [re.compile(p.pattern.encode("ascii"), p.flags & ~re.UNICODE) for p in SIGNED_URL_PATTERNS]),
                ("secret pattern", [re.compile(p.pattern.encode("ascii"), p.flags & ~re.UNICODE) for p in SECRET_PATTERNS]),
            )
            for category, patterns in groups_b:
                if any(pattern.search(raw) for pattern in patterns):
                    report.fail(f"public safety: {category} in binary file {relative(path)}")
                    findings += 1
    report.note(f"public scan checked {text_files} UTF-8 files and {binary_files} binary files; no public files silently skipped")
    if ignored:
        report.note("ignored paths excluded by repository rules: " + ", ".join(ignored))
    if not findings and not symlinks:
        report.ok("public files contain no detected local username paths, private provider IDs, signed URLs, or secret patterns")


def main() -> int:
    report = Report()
    if not ROOT.is_dir():
        print(f"FAIL  project root not found: {ROOT}")
        return 2
    check_frozen_v11(report)
    check_unchanged_app_and_mascot(report)
    check_manifest_pair(report)
    check_markdown_references(report)
    check_html_resources(report)
    check_capture_comparison(report)
    check_capture_comparison(report, "v1.2.0", "v2.1.0", "comparison-2.1.json")
    report_public_safety(report)
    return report.finish()


if __name__ == "__main__":
    raise SystemExit(main())
