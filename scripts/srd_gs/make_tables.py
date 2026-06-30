import argparse
import csv
import os


def read_rows(path):
    with open(path, "r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_markdown_table(rows):
    header = "| scene | variant | metric | value | not_available_reason |\n| --- | --- | --- | --- | --- |"
    lines = [header]
    for row in rows:
        lines.append(
            "| {scene} | {variant} | {name} | {value} | {reason} |".format(
                scene=row.get("scene", ""),
                variant=row.get("variant", ""),
                name=row.get("name", ""),
                value=row.get("value", ""),
                reason=row.get("not_available_reason", ""),
            )
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Create markdown tables from SRD-GS ablation metrics CSV")
    parser.add_argument("--metrics_csv", required=True)
    parser.add_argument("--output_md", required=True)
    args = parser.parse_args()

    rows = read_rows(args.metrics_csv)
    os.makedirs(os.path.dirname(args.output_md) or ".", exist_ok=True)
    with open(args.output_md, "w", encoding="utf-8") as handle:
        handle.write("# SRD-GS Ablation Metrics Table\n\n")
        handle.write(make_markdown_table(rows))
    print("Wrote table:", args.output_md)


if __name__ == "__main__":
    main()
