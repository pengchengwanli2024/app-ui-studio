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
    def test_design_system_defaults_to_brief_and_only_targets_specification(self):
        brief = self.read('--focus', 'design-system', '--scope', 'existing')
        self.assertEqual(brief['task'], 'brief')
        self.assertFalse(brief['execution']['project_writes'])
        self.assertFalse(brief['execution']['implementation'])
        self.assertFalse(brief['execution']['product_changes'])
        self.assertTrue(brief['design_system']['existing_authority_first'])
        self.assertFalse(brief['design_system']['brand_values_adopted'])
        for task in ('design', 'polish'):
            data = self.read('--focus', 'design-system', '--task', task, '--scope', 'existing')
            self.assertTrue(data['execution']['project_writes'])
            self.assertFalse(data['execution']['implementation'])
            self.assertFalse(data['execution']['product_changes'])
            self.assertEqual(data['deliverable'], 'design-system-spec')
            self.assertNotIn('engineering_contract', data)
            self.assertIn('visual-system', data['preserve'])
        audit = self.read('--focus', 'design-system', '--task', 'audit')
        self.assertFalse(audit['execution']['project_writes'])
        self.assertEqual(audit['recommended_directions'], 0)

    def test_engineering_contract_is_scoped_and_preserves_read_only_modes(self):
        extended = self.read('--task', 'extend', '--scope', 'existing', '--domain', 'workspace')
        contract = extended['engineering_contract']
        self.assertEqual(contract['mode'], 'implement')
        self.assertEqual(len(contract['fields']), 8)
        self.assertIn('actor_permissions', contract['fields'])
        self.assertIn('failure_recovery', contract['fields'])
        self.assertFalse(contract['backend_creation_required'])
        self.assertFalse(contract['contract_verified'])
        self.assertTrue(contract['only_applicable_layers'])
        for task, mode in [('audit', 'observe'), ('brief', 'plan')]:
            data = self.read('--focus', 'frontend', '--task', task)
            self.assertEqual(data['engineering_contract']['mode'], mode)
            self.assertFalse(data['execution']['implementation'])
            self.assertFalse(data['execution']['project_writes'])
        for args in [('--task', 'polish', '--focus', 'component'),
                     ('--task', 'extend', '--focus', 'media'),
                     ('--task', 'extend', '--surface', 'marketing')]:
            self.assertNotIn('engineering_contract', self.read(*args))

    def test_new_guidance_does_not_read_or_overwrite_project_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / 'DESIGN.md'
            sentinel.write_bytes(b'Existing private brand and rules')
            for args in [('--focus', 'design-system'), ('--focus', 'design-system', '--task', 'design'),
                         ('--task', 'extend', '--scope', 'existing')]:
                data = json.loads(invoke(*args, '--format', 'json', cwd=directory).stdout)
                self.assertFalse(data['project_inspected'])
                self.assertEqual(list(Path(directory).iterdir()), [sentinel])
                self.assertEqual(sentinel.read_bytes(), b'Existing private brand and rules')
                self.assertNotIn('Existing private brand', data['prompt'])

    def test_web_quality_defaults_to_read_only_and_preserves_platform_boundary(self):
        data = self.read('--focus', 'web-quality', '--platform', 'mobile')
        self.assertEqual(data['task'], 'audit')
        self.assertFalse(data['execution']['project_writes'])
        self.assertFalse(data['execution']['implementation'])
        self.assertFalse(data['project_inspected'])
        for platform in ('native-ios', 'native-android', 'mini-program'):
            invoke('--focus', 'web-quality', '--platform', platform, expected=2)

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

    def test_specialties_preserve_read_only_and_existing_scope(self):
        for focus in ("component", "media", "motion", "scroll", "explore", "iterate"):
            data = self.read("--task", "audit", "--focus", focus)
            self.assertEqual(data["focus"], focus)
            self.assertFalse(data["execution"]["implementation"])
            self.assertFalse(data["execution"]["project_writes"])
            self.assertEqual(data["recommended_directions"], 0)
            self.assertTrue(data["specialty"]["reference"].endswith(".md"))
        component = self.read("--task", "polish", "--domain", "workspace", "--scope", "existing", "--focus", "component")
        self.assertIn("visual-system", component["preserve"])
        self.assertEqual(component["specialty"]["mode"], "functional")

    def test_media_brief_does_not_request_product_implementation(self):
        data = self.read("--task", "brief", "--focus", "media", "--domain", "persuasion", "--surface", "marketing")
        self.assertFalse(data["execution"]["implementation"])
        self.assertFalse(data["execution"]["project_writes"])
        self.assertEqual(data["deliverable"], "brief")
        self.assertFalse(data["generation_executed"])

    def test_exploration_is_explicit_and_counts_are_respected(self):
        data = self.read("--focus", "explore", "--directions", "4")
        self.assertEqual(data["recommended_directions"], 4)
        self.assertEqual(self.read("--focus", "explore")["recommended_directions"], 3)
        for arguments in (("--directions", "3"), ("--focus", "explore", "--directions", "1"),
                          ("--focus", "scroll", "--domain", "workspace")):
            invoke(*arguments, expected=2)
        data = self.read("--focus", "scroll", "--domain", "workspace", "--surface", "both")
        self.assertEqual(data["specialty"]["applies_to"], ["persuasion"])
        audit = self.read("--task", "audit", "--focus", "scroll", "--domain", "workspace")
        self.assertFalse(audit["execution"]["project_writes"])
        self.assertEqual(audit["specialty"]["applies_to"], ["workspace"])


if __name__ == "__main__":
    unittest.main()
