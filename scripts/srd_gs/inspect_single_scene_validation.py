#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.geometry_eval_utils import (
    build_geometry_protocol,
    inspect_blender_split_policy,
)
from utils.srd_branch_policy import get_srd_branch_map_policy


def _scene_name(source_path):
    return os.path.basename(os.path.abspath(source_path.rstrip(os.sep)))


def _build_split_gate(source_path, eval_flag):
    policy = inspect_blender_split_policy(source_path, eval_flag=eval_flag)
    return {
        "eval_flag": bool(eval_flag),
        "train_frames": policy["effective_train_frames"],
        "test_frames": policy["effective_test_frames"],
        "test_split_ready": policy["effective_test_frames"] > 0,
        "empty_test_reason": policy["empty_test_reason"],
        "raw_policy": policy,
    }


def _build_gt_geometry_gate(source_path):
    protocol = build_geometry_protocol(source_path)
    points_policy = protocol.get("points3d_source_policy", {})
    reason = protocol.get("not_available_reason")
    if protocol["acceptance_status"] != "accepted_gt" and points_policy.get("source_evidence"):
        reason = "{}; {}".format(reason, points_policy["source_evidence"])
    return {
        "candidate_gt_geometry_path": protocol["candidate_gt_geometry_path"],
        "candidate_exists": protocol["candidate_exists"],
        "gt_geometry_type": protocol["gt_geometry_type"],
        "accepted_gt_source": protocol.get("accepted_gt_source"),
        "acceptance_status": protocol["acceptance_status"],
        "accepted_gt_ready": protocol["acceptance_status"] == "accepted_gt",
        "raw_coordinate_evaluation": protocol["raw_coordinate_evaluation"],
        "icp_enabled_by_default": protocol["icp_enabled_by_default"],
        "reason": reason,
        "raw_protocol": protocol,
    }


def _build_branch_map_gate(enable_srd_gs):
    if not enable_srd_gs:
        return {
            "enable_srd_gs": False,
            "branch_maps_required": False,
            "branch_maps_rasterized": None,
            "policy": {"policy": "baseline_no_srd"},
        }
    policy = get_srd_branch_map_policy(use_branch_gate_requested=True)
    branch_maps_rasterized = all(
        policy[name]["rasterized"]
        for name in ("branch_gate_map", "specular_weight_map", "transport_feature_map")
    )
    return {
        "enable_srd_gs": True,
        "branch_maps_required": True,
        "branch_maps_rasterized": branch_maps_rasterized,
        "policy": policy,
    }


def _build_paper_scale_gate(split_gate, gt_geometry_gate, branch_map_gate):
    blockers = []
    if not split_gate["test_split_ready"]:
        blockers.append("test_split_unavailable")
    if not gt_geometry_gate["accepted_gt_ready"]:
        blockers.append("accepted_gt_geometry_unavailable")
    if branch_map_gate["enable_srd_gs"] and not branch_map_gate["branch_maps_rasterized"]:
        blockers.append("srd_branch_maps_not_rasterized")
    return {
        "allowed": len(blockers) == 0,
        "status": "GO" if len(blockers) == 0 else "NO-GO",
        "blockers": blockers,
    }


def build_single_scene_validation_report(source_path, eval_flag, enable_srd_gs):
    split_gate = _build_split_gate(source_path, eval_flag)
    gt_geometry_gate = _build_gt_geometry_gate(source_path)
    branch_map_gate = _build_branch_map_gate(enable_srd_gs)
    paper_scale_gate = _build_paper_scale_gate(split_gate, gt_geometry_gate, branch_map_gate)
    return {
        "schema_version": 1,
        "milestone": 12,
        "scene": _scene_name(source_path),
        "source_path": os.path.abspath(source_path),
        "split_gate": split_gate,
        "gt_geometry_gate": gt_geometry_gate,
        "branch_map_gate": branch_map_gate,
        "paper_scale_gate": paper_scale_gate,
        "recommended_next_actions": [
            "Train or regenerate one-scene checkpoints with eval=True before test-split metrics.",
            "Use explicit scene GT mesh files for raw-coordinate geometry metrics; keep dataset-generated points3d.ply rejected by default.",
            "Implement true SRD branch-map rasterization before claiming branch-gate/specular-weight training behavior.",
            "Keep broad paper-scale experiments blocked until all gates are GO.",
        ],
    }


def _write_markdown(report, output_dir):
    path = Path(output_dir) / "single_scene_validation_report.md"
    split_gate = report["split_gate"]
    gt_gate = report["gt_geometry_gate"]
    branch_gate = report["branch_map_gate"]
    paper_gate = report["paper_scale_gate"]
    lines = [
        "# Milestone 12 Single-scene Validation Gate",
        "",
        "Scene: `{}`".format(report["scene"]),
        "",
        "## Split Gate",
        "",
        "- eval flag: `{}`".format(split_gate["eval_flag"]),
        "- effective train frames: `{}`".format(split_gate["train_frames"]),
        "- effective test frames: `{}`".format(split_gate["test_frames"]),
        "- test split ready: `{}`".format(split_gate["test_split_ready"]),
        "- empty test reason: `{}`".format(split_gate["empty_test_reason"]),
        "",
        "## GT Geometry Gate",
        "",
        "- candidate path: `{}`".format(gt_gate["candidate_gt_geometry_path"]),
        "- candidate exists: `{}`".format(gt_gate["candidate_exists"]),
        "- acceptance status: `{}`".format(gt_gate["acceptance_status"]),
        "- accepted GT ready: `{}`".format(gt_gate["accepted_gt_ready"]),
        "- reason: {}".format(gt_gate["reason"]),
        "",
        "## Branch-map Gate",
        "",
        "- enable SRD-GS: `{}`".format(branch_gate["enable_srd_gs"]),
        "- branch maps rasterized: `{}`".format(branch_gate["branch_maps_rasterized"]),
        "",
        "## Paper-scale Gate",
        "",
        "- Paper-scale gate: {}".format(paper_gate["status"]),
        "- blockers: `{}`".format(", ".join(paper_gate["blockers"]) or "none"),
        "",
        "## Recommended Next Actions",
        "",
    ]
    lines.extend("- {}".format(action) for action in report["recommended_next_actions"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def write_single_scene_validation_report(report, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "single_scene_validation_report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path = _write_markdown(report, output)
    return str(json_path), md_path


def main():
    parser = argparse.ArgumentParser(description="Inspect SRD-GS single-scene validation gates")
    parser.add_argument("--source_path", required=True)
    parser.add_argument("--output_dir", default="outputs/srd_gs_validation")
    parser.add_argument("--eval", action="store_true", default=False, help="Inspect split policy with eval=True")
    parser.add_argument("--enable_srd_gs", action="store_true", default=False)
    args = parser.parse_args()

    report = build_single_scene_validation_report(
        source_path=args.source_path,
        eval_flag=args.eval,
        enable_srd_gs=args.enable_srd_gs,
    )
    json_path, md_path = write_single_scene_validation_report(report, args.output_dir)
    print("Wrote validation JSON:", json_path)
    print("Wrote validation Markdown:", md_path)
    print("Paper-scale gate:", report["paper_scale_gate"]["status"])


if __name__ == "__main__":
    main()
