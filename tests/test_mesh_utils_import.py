import unittest


class MeshUtilsImportTest(unittest.TestCase):
    def test_mesh_utils_imports(self):
        import utils.mesh_utils as mesh_utils

        self.assertTrue(hasattr(mesh_utils, "GaussianExtractor"))
        self.assertTrue(hasattr(mesh_utils, "post_process_mesh"))
        self.assertTrue(hasattr(mesh_utils, "to_cam_open3d"))


if __name__ == "__main__":
    unittest.main()
