"""Portable screenshot board: comparability, safe input and non-overwrite behavior."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from fixtures import png

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py"


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("a", "b"):
            (self.root / (name + ".png")).write_bytes(png(2, 1))
        self.manifest = {"schema_version": 1, "title": "首屏版式比较", "context": {"state": "initial", "locale": "zh-CN"},
                         "candidates": [{"id": name, "label": name, "note": "同一品牌，不同版式", "screens": [
                             {"id": "desktop", "artifact": name + ".png", "viewport": {"width": 2, "height": 1}}]}
                             for name in ("a", "b")]}
        self.input = self.root / "input.json"
        self.output = self.root / "board"

    def invoke(self, data=None, expected=0):
        self.input.write_text(json.dumps(data or self.manifest, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "board", str(self.input), "--output", str(self.output)],
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stderr.decode("utf-8", "replace"))
        self.assertNotIn(b"Traceback", result.stderr)
        return json.loads(result.stdout)

    def test_portable_artifacts_and_honest_receipt(self):
        result = self.invoke()
        self.assertTrue(result["artifact_contract_valid"])
        self.assertFalse(result["visual_quality_verified"])
        self.assertFalse(result["selection_applied"])
        self.assertFalse(result["generation_executed"])
        self.assertTrue((self.output / "index.html").is_file())
        data = json.loads((self.output / "board.json").read_text(encoding="utf-8"))
        for candidate in data["candidates"]:
            screen = candidate["screens"][0]
            raw = (self.output / screen["artifact"]).read_bytes()
            self.assertEqual(screen["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(raw, (self.root / (candidate["id"] + ".png")).read_bytes())

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        marker = self.output / "keep"
        marker.write_text("preserve", encoding="utf-8")
        self.invoke(expected=2)
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(list(self.output.iterdir()), [marker])

    def test_invalid_inputs_create_no_output(self):
        for mutate in (lambda d: d["candidates"].pop(),
                       lambda d: d["candidates"][1].update(id="a"),
                       lambda d: d["candidates"][1]["screens"][0].update(id="other"),
                       lambda d: d["candidates"][1]["screens"][0]["viewport"].update(width=3),
                       lambda d: d["candidates"][0]["screens"][0].update(artifact="../a.png"),
                       lambda d: d["candidates"][0]["screens"][0].update(artifact=str(self.root / "a.png")),
                       lambda d: d["candidates"][0].update(url="javascript:alert(1)")):
            data = copy.deepcopy(self.manifest)
            mutate(data)
            self.invoke(data, expected=2)
            self.assertFalse(self.output.exists())

    def test_untrusted_labels_are_data(self):
        self.manifest["title"] = '</script><script>alert("label")</script>'
        self.manifest["candidates"][0]["label"] = '<img src=x onerror=alert(1)>'
        self.invoke()
        page = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertNotIn(self.manifest["title"], page)
        self.assertNotIn(self.manifest["candidates"][0]["label"], page)


if __name__ == "__main__":
    unittest.main()
