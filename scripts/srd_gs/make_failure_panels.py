import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Create a failure-panel index for SRD-GS ablation outputs")
    parser.add_argument("--results_root", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    index_path = os.path.join(args.output_dir, "failure_panel_index.md")
    entries = []
    for current_root, dirs, files in os.walk(args.results_root):
        if "metrics.json" in files or "reflective_mask.png" in files:
            entries.append(os.path.relpath(current_root, args.results_root))
    with open(index_path, "w", encoding="utf-8") as handle:
        handle.write("# SRD-GS Failure Panel Index\n\n")
        if not entries:
            handle.write("No failure-panel source artifacts found.\n")
        for entry in sorted(entries):
            handle.write("- `{}`\n".format(entry))
    print("Wrote failure panel index:", index_path)


if __name__ == "__main__":
    main()
