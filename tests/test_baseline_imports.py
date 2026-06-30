import importlib
import unittest


class BaselineImportsTest(unittest.TestCase):
    def test_core_modules_import(self):
        modules = [
            "scene.gaussian_model",
            "gaussian_renderer",
            "utils.loss_utils",
            "utils.mesh_utils",
        ]
        for module_name in modules:
            with self.subTest(module=module_name):
                importlib.import_module(module_name)


if __name__ == "__main__":
    unittest.main()
