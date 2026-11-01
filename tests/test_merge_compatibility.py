"""Regression checks for restoring the frozen 2.0 prompt-library surface in 2.1.

The JSON fixture pins independently captured outputs from the private 2.0 source,
so CI does not need that private source tree.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/app-ui-studio/skills/app-ui-studio"
STUDIO = SKILL / "scripts/studio.py"
FIXTURE = json.loads((Path(__file__).parent / "fixtures-v2.json").read_text(encoding="utf-8"))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def invoke(*args: str, expected: int = 0) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, str(STUDIO), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == expected, (
        args,
        result.returncode,
        result.stdout.decode("utf-8", "replace"),
        result.stderr.decode("utf-8", "replace"),
    )
    assert b"Traceback" not in result.stderr, (args, result.stderr)
    return result


def test_help_exposes_full_cli() -> None:
    result = invoke("--help")
    help_text = result.stdout.decode("utf-8")
    groups = re.findall(r"\{([^}]+)\}", help_text)
    commands = set(groups[0].replace("\n", " ").split(",")) if groups else set()
    assert commands == {
        "catalog", "prompt", "export-prompts", "doctor", "contrast",
        "init", "preset", "check", "compare",
    }, help_text


def test_frozen_source_identity() -> None:
    for relative, expected in FIXTURE["source_hashes"].items():
        actual = (SKILL / relative).read_bytes()
        if relative == "scripts/prompt_library.py":
            # The only approved 2.1 change is the exported archive's own version label.
            marker = b'"version":"2.1.0"'
            assert actual.count(marker) == 1, "expected exactly one 2.1 export version literal"
            actual = actual.replace(marker, b'"version":"2.0.0"')
        assert sha256(actual) == expected, f"frozen source changed: {relative}"


def test_standalone_and_paired_outputs() -> None:
    catalog_entries = {}
    for kind in ("software", "industry"):
        catalog = invoke("catalog", "--kind", kind)
        assert sha256(catalog.stdout) == FIXTURE["catalog_cli_sha256"][kind]
        assert b"\r\n" not in catalog.stdout, "JSON CLI output must use stable LF newlines"
        data = json.loads(catalog.stdout)
        entries = data["catalogs"][kind]
        assert [item["id"] for item in entries] == FIXTURE["catalog_ids"][kind]
        assert len(entries) == (20 if kind == "software" else 16)
        catalog_entries[kind] = {item["id"]: item["label"] for item in entries}

    for kind in ("software", "industry"):
        for identifier in FIXTURE["catalog_ids"][kind]:
            result = invoke("prompt", f"--{kind}", identifier, "--format", "json")
            key = f"{kind}/{identifier}.md"
            assert sha256(result.stdout) == FIXTURE["prompt_cli_sha256"][key], key
            prompt = json.loads(result.stdout)["prompt"].encode("utf-8")
            assert sha256(prompt) == FIXTURE["prompt_content_sha256"][key], key

    software_ids = FIXTURE["catalog_ids"]["software"]
    industry_ids = FIXTURE["catalog_ids"]["industry"]
    assert len(FIXTURE["paired_prompt_cli_sha256"]) == 20
    paired_industries = set()
    for index, software_id in enumerate(software_ids):
        industry_id = industry_ids[index % len(industry_ids)]
        paired_industries.add(industry_id)
        key = f"{software_id}+{industry_id}"
        result = invoke(
            "prompt", "--software", software_id, "--industry", industry_id,
            "--scope", "existing", "--surface", "both", "--tone", "tech-refined",
            "--format", "json",
        )
        assert sha256(result.stdout) == FIXTURE["paired_prompt_cli_sha256"][key], key
        output = json.loads(result.stdout)
        assert output["software"] == software_id and output["industry"] == industry_id
        assert output["scope"] == "existing" and output["surface"] == "both"
        assert output["tone"] == "tech-refined"
        assert f"软件类型：{catalog_entries['software'][software_id]}" in output["prompt"]
        assert f"行业：{catalog_entries['industry'][industry_id]}" in output["prompt"]
        assert "## 软件任务与界面" in output["prompt"]
        assert "## 行业流程与边界" in output["prompt"]
    assert paired_industries == set(industry_ids), "paired coverage must include all 16 industries"


def test_scope_surface_and_tone_change_prompt() -> None:
    base_args = (
        "prompt", "--software", "personal-productivity", "--scope", "auto",
        "--surface", "both", "--tone", "tech-refined", "--format", "json",
    )
    base = json.loads(invoke(*base_args).stdout)
    assert base["industry"] is None
    for name, values in (
        ("scope", ("new", "existing", "mixed")),
        ("surface", ("product", "marketing")),
        ("tone", ("calm", "tech-expressive")),
    ):
        for value in values:
            args = list(base_args)
            args[args.index("--" + name) + 1] = value
            changed = json.loads(invoke(*args).stdout)
            assert changed[name] == value
            assert changed["prompt"] != base["prompt"], f"{name}={value} had no effect"


def test_exported_templates_match_frozen_content() -> None:
    with tempfile.TemporaryDirectory(prefix="app-ui-studio-merge-export-") as temporary:
        destination = Path(temporary) / "prompts"
        result = invoke("export-prompts", "--output", str(destination))
        response = json.loads(result.stdout)
        assert response["prompt_count"] == 36
        # Markdown text has platform-native newlines; retain frozen UTF-8 content
        # hashes after universal-newline decoding. JSON CLI bytes stay exact above.
        files = {
            path.relative_to(destination).as_posix(): sha256(path.read_text(encoding="utf-8").encode("utf-8"))
            for path in destination.rglob("*.md")
            if path.name != "README.md"
        }
        assert files == FIXTURE["export_markdown_sha256"]
        manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["version"] == "2.1.0"
        assert len(manifest["files"]) == 36


def test_export_refuses_existing_targets_and_missing_parent() -> None:
    with tempfile.TemporaryDirectory(prefix="app-ui-studio-merge-safety-") as temporary:
        root = Path(temporary)

        existing_dir = root / "existing-dir"
        existing_dir.mkdir()
        sentinel = existing_dir / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        invoke("export-prompts", "--output", str(existing_dir), expected=2)
        assert sentinel.read_text(encoding="utf-8") == "keep"
        assert sorted(path.name for path in existing_dir.iterdir()) == ["keep.txt"]

        existing_file = root / "existing-file"
        existing_file.write_bytes(b"preserve exact bytes")
        invoke("export-prompts", "--output", str(existing_file), expected=2)
        assert existing_file.read_bytes() == b"preserve exact bytes"

        symlink_target = root / "symlink-target"
        symlink_target.mkdir()
        target_sentinel = symlink_target / "keep.txt"
        target_sentinel.write_text("keep target", encoding="utf-8")
        symlink = root / "existing-symlink"
        symlink.symlink_to(symlink_target, target_is_directory=True)
        invoke("export-prompts", "--output", str(symlink), expected=2)
        assert symlink.is_symlink()
        assert target_sentinel.read_text(encoding="utf-8") == "keep target"
        assert sorted(path.name for path in symlink_target.iterdir()) == ["keep.txt"]

        absent_parent = root / "does-not-exist"
        absent_destination = absent_parent / "prompts"
        invoke("export-prompts", "--output", str(absent_destination), expected=2)
        assert not absent_parent.exists()
        assert not absent_destination.exists()


def main() -> None:
    checks = (
        test_frozen_source_identity,
        test_standalone_and_paired_outputs,
        test_scope_surface_and_tone_change_prompt,
        test_exported_templates_match_frozen_content,
        test_export_refuses_existing_targets_and_missing_parent,
        test_help_exposes_full_cli,
    )
    for check in checks:
        check()
    print("PASS 6 merge compatibility groups; 36 standalone + 20 paired prompt outputs, exports, safety and all 9 CLI commands checked")


if __name__ == "__main__":
    main()
