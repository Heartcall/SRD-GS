import tempfile
import unittest
from pathlib import Path

import numpy as np

from utils.render_utils import save_img_u8


class RenderUtilsImageIOTest(unittest.TestCase):
    def test_save_img_u8_accepts_single_channel_hwc_png(self):
        image = np.ones((4, 5, 1), dtype=np.float32)
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "single_channel.png"
            save_img_u8(image, str(path))
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
