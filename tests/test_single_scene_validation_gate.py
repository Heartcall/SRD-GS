import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "srd_gs" / "inspect_single_scene_validation.py"
BALL_PATH = "/data/liuly/dataset/3DGS/Shiny Blender Synthetic/ball"


def _load_module():
    spec = importlib.util.spec_from_file_location("inspect_single_scene_validation", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SingleSceneValidationGateTest(unittest.TestCase):
    def test_ball_eval_split_ready_but_dataset_points3d_does_not_unlock_paper_scale(self):
        module = _load_module()

        report = module.build_single_scene_validation_report(
            source_path=BALL_PATH,
            eval_flag=True,
            enable_srd_gs=True,
        )

        self.assertEqual(report["scene"], "ball")
        self.assertTrue(report["split_gate"]["test_split_ready"])
        self.assertEqual(report["split_gate"]["test_frames"], 200)
        self.assertFalse(report["gt_geometry_gate"]["accepted_gt_ready"])
        self.assertEqual(report["gt_geometry_gate"]["acceptance_status"], "not_accepted_gt")
        self.assertIn("random point cloud", report["gt_geometry_gate"]["reason"])
        self.assertFalse(report["paper_scale_gate"]["allowed"])
        self.assertIn("accepted_gt_geometry_unavailable", report["paper_scale_gate"]["blockers"])
        self.assertIn("srd_branch_maps_not_rasterized", report["paper_scale_gate"]["blockers"])

    def test_report_writer_emits_json_and_markdown(self):
        module = _load_module()

        report = module.build_single_scene_validation_report(
            source_path=BALL_PATH,
            eval_flag=False,
            enable_srd_gs=False,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_path, md_path = module.write_single_scene_validation_report(report, tmp_dir)

            self.assertTrue(Path(json_path).exists())
            markdown = Path(md_path).read_text(encoding="utf-8")
            self.assertIn("Milestone 12 Single-scene Validation Gate", markdown)
            self.assertIn("eval_false_merges_test_into_train", markdown)
            self.assertIn("Paper-scale gate: NO-GO", markdown)

    def test_script_file_entrypoint_runs_from_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--source_path",
                    BALL_PATH,
                    "--eval",
                    "--enable_srd_gs",
                    "--output_dir",
                    tmp_dir,
                ],
                cwd=str(ROOT),
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((Path(tmp_dir) / "single_scene_validation_report.json").exists())


if __name__ == "__main__":
    unittest.main()
