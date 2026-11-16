"""Observable contracts for scoped workflow prompts; no model or provider calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py"


def invoke(*arguments, expected=0, cwd=None):
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), "workflow", *arguments],
                            cwd=cwd or ROOT, capture_output=True, timeout=15)
    if result.returncode != expected:
        raise AssertionError(result.stderr.decode("utf-8", "replace"))
    return result


class WorkflowTests(unittest.TestCase):
    def read(self, *arguments):
        return json.loads(invoke(*arguments, "--format", "json").stdout)

    def test_audit_is_read_only_even_with_new_scope(self):
        data = self.read("--task", "audit", "--domain", "content", "--scope", "new")
        self.assertFalse(data["execution"]["project_writes"])
        self.assertFalse(data["execution"]["implementation"])
        self.assertEqual(data["review_mode"], "evidence-only")
        self.assertEqual(data["domains"], ["content"])
        self.assertEqual(data["recommended_directions"], 0)
        self.assertEqual(data["tone"], "auto")

    def test_existing_extension_preserves_visual_system(self):
        data = self.read("--task", "extend", "--domain", "workspace", "--scope", "existing")
        self.assertTrue(data["execution"]["implementation"])
        self.assertIn("visual-system", data["preserve"])
        self.assertEqual(data["review_mode"], "baseline-comparison")

    def test_both_surfaces_keep_domains_separate(self):
        data = self.read("--domain", "content", "--surface", "both", "--platform", "cross-platform")
        self.assertEqual(data["domains"], ["content", "persuasion"])
        self.assertEqual(data["suggested_viewports"], [{"width": 1440, "height": 900}, {"width": 390, "height": 844}])
        self.assertEqual(data["recommended_directions"], 1)

    def test_target_devices_do_not_invent_native_evidence(self):
        mobile = self.read("--platform", "mobile")
        native = self.read("--platform", "native-ios")
        self.assertEqual(mobile["suggested_viewports"], [{"width": 390, "height": 844}])
        self.assertEqual(native["suggested_viewports"], [])
        for data in (mobile, native):
            self.assertFalse(data["project_inspected"])
            self.assertFalse(data["generation_executed"])
            self.assertFalse(data["ui_quality_verified"])
            self.assertFalse(data["independent_review_executed"])

    def test_catalog_composition_and_markdown_share_one_result(self):
        arguments = ("--software", "ai-agent", "--industry", "manufacturing", "--domain", "workspace")
        data = self.read(*arguments)
        self.assertEqual(data["software"], "ai-agent")
        self.assertEqual(data["industry"], "manufacturing")
        self.assertEqual(invoke(*arguments).stdout.decode("utf-8"), data["prompt"])

    def test_invalid_routes_and_ids_are_rejected(self):
        for arguments in (("--task", "unknown"), ("--domain", "unknown"),
                          ("--software", "missing"), ("--industry", "missing"),
                          ("--surface", "marketing", "--domain", "workspace")):
            result = invoke(*arguments, expected=2)
            self.assertNotIn(b"Traceback", result.stderr)

    def test_generator_does_not_write_or_inspect_target_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "DESIGN.md"
            marker.write_bytes(b"private project sentinel")
            before = {p.name: p.read_bytes() for p in Path(directory).iterdir()}
            data = json.loads(invoke("--format", "json", cwd=directory).stdout)
            self.assertFalse(data["project_inspected"])
            self.assertEqual(before, {p.name: p.read_bytes() for p in Path(directory).iterdir()})
            self.assertNotIn("private project sentinel", data["prompt"])


if __name__ == "__main__":
    unittest.main()
