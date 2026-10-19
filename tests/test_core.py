"""Non-invasive checks for the BASKA SEND single-file application."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("SendToCom", ROOT / "SendToCom.py")
APP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = APP
SPEC.loader.exec_module(APP)


class CoreTests(unittest.TestCase):
    def test_version(self):
        self.assertRegex(APP.VERSION, r"^\d+\.\d+\.\d+$")

    def test_pin_hash(self):
        salt = b"0123456789abcdef"
        self.assertEqual(APP.pin_hash("12345678", salt), APP.pin_hash("12345678", salt))
        self.assertNotEqual(APP.pin_hash("12345678", salt), APP.pin_hash("87654321", salt))

    def test_safe_filename(self):
        self.assertEqual(APP.safe_filename("../hello?.pdf"), "hello_.pdf")
        self.assertEqual(APP.safe_filename(""), "file")

    def test_allowed_files(self):
        cfg = {"allowed_extensions": APP.DEFAULT_ALLOWED_EXTENSIONS}
        self.assertTrue(APP.file_allowed(cfg, "sample.pdf", b"%PDF-1.7\n")[0])
        self.assertFalse(APP.file_allowed(cfg, "sample.pdf", b"not a PDF")[0])
        self.assertFalse(APP.file_allowed(cfg, "program.exe", b"MZ")[0])
        self.assertFalse(APP.file_allowed(cfg, "photo.jpg", b"MZfake")[0])

    def test_path_containment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inbox = root / "inbox"
            inbox.mkdir()
            self.assertTrue(APP._is_within(inbox / "file.txt", inbox))
            self.assertFalse(APP._is_within(root / "elsewhere.txt", inbox))


if __name__ == "__main__":
    unittest.main()
