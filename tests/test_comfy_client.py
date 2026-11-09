"""รันด้วย: python -m unittest discover tests"""

import importlib.util
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from comfy_client import NO_CHECKPOINT_MESSAGE, describe_comfy_rejection, describe_execution_error  # noqa: E402


def load_ad_studio():
    spec = importlib.util.spec_from_file_location("ad_studio", ROOT_DIR / "07-product-ad-studio" / "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DescribeComfyFailureTest(unittest.TestCase):
    def test_missing_checkpoint_tells_student_where_to_put_the_model(self):
        payload = {
            "error": {"type": "prompt_outputs_failed_validation", "message": "Prompt outputs failed validation"},
            "node_errors": {
                "4": {
                    "errors": [
                        {
                            "type": "value_not_in_list",
                            "message": "Value not in list",
                            "details": "ckpt_name: 'v1-5-pruned-emaonly.safetensors' not in []",
                            "extra_info": {"input_name": "ckpt_name"},
                        }
                    ],
                    "class_type": "CheckpointLoaderSimple",
                }
            },
        }
        self.assertEqual(describe_comfy_rejection(payload), NO_CHECKPOINT_MESSAGE)

    def test_missing_custom_node_names_the_node(self):
        payload = {
            "error": {
                "type": "missing_node_type",
                "message": "Node 'AnimateDiff Loader' not found.",
                "extra_info": {"class_type": "ADE_AnimateDiffLoaderWithContext"},
            },
            "node_errors": {},
        }
        self.assertIn("ADE_AnimateDiffLoaderWithContext", describe_comfy_rejection(payload))

    def test_execution_error_reports_the_failing_node(self):
        status = {
            "status_str": "error",
            "messages": [
                ["execution_start", {}],
                ["execution_error", {"node_type": "KSampler", "exception_message": "out of memory\n"}],
            ],
        }
        self.assertEqual(describe_execution_error(status), "ComfyUI รันโหนด KSampler ไม่สำเร็จ: out of memory")


class RemovePlainBackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.studio = load_ad_studio()

    def test_white_background_becomes_transparent_and_is_cropped_to_product(self):
        photo = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
        photo.paste((200, 20, 20, 255), (50, 60, 150, 140))

        result = self.studio.remove_plain_background(photo)

        self.assertEqual(result.size, (100, 80))
        self.assertEqual(result.getpixel((50, 40))[3], 255)

    def test_image_with_existing_transparency_is_returned_unchanged(self):
        cutout = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
        self.assertIs(self.studio.remove_plain_background(cutout), cutout)

    def test_expand_to_three_shots_fills_missing_angles(self):
        one_shot = Image.new("RGBA", (50, 50), (10, 20, 30, 255))
        self.assertEqual(len(self.studio.expand_to_three_shots([one_shot])), 3)


if __name__ == "__main__":
    unittest.main()
