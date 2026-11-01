# Preserved experiment inputs

`spec.md`, `check.py`, `validate.py` and `fixtures.py` are the original frozen experiment inputs. `baseline/studio.py` is the original 1.2.0 command implementation. Their identity is recorded in `evidence/harness/summary.json`; the shipped 1.3.0 script is separately verified.

Use `python3 scripts/replay_harness.py` from the repository root to replay the four retained patches in disposable directories. This performs no model calls. It reproduces 42 contract checks per condition and the adopted baseline's 34 independent boundary checks.

`jpeg_supplement.py` is the unchanged supplementary checker retained for provenance. Its original execution depends on the local, unpublished `.harness2` workspaces. The uniform results, real-image hashes and checker hash are preserved in the public summary. It is not a standalone clone/CI entrypoint. The ordinary public contract tests use a corrected owned-pixel JPEG fixture; neither checker promises full image decoding or visual-quality evaluation.
