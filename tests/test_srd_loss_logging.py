from pathlib import Path
import csv
import tempfile
import unittest

from train import SRD_LOSS_LOG_FIELDS, append_srd_loss_log_row


class SRDLossLoggingTest(unittest.TestCase):
    def test_appends_csv_header_once_with_stable_fields(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            loss_log = Path(tmp_dir) / "nested" / "loss_log.csv"
            row = {field: 0 for field in SRD_LOSS_LOG_FIELDS}
            row["iteration"] = 10
            row["stage"] = "stage_a"
            row["gaussian_count"] = 100000

            append_srd_loss_log_row(loss_log, row)
            row["iteration"] = 20
            append_srd_loss_log_row(loss_log, row)

            with loss_log.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(SRD_LOSS_LOG_FIELDS, list(rows[0].keys()))
        self.assertEqual([row["iteration"] for row in rows], ["10", "20"])
        self.assertEqual(rows[0]["stage"], "stage_a")


if __name__ == "__main__":
    unittest.main()
