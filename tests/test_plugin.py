import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from plugin_run import run

class PluginContractTests(unittest.TestCase):
    def test_example_round_trip(self):
        data = json.loads((ROOT / "examples/plugin-input.json").read_text(encoding="utf-8"))
        result = run(data)
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["result"]["markdown"].strip())
        schema = json.loads((ROOT / "schemas/output.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(result)

    def test_invalid_input_is_structured_and_nonzero(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/plugin_run.py")], input="{}", text=True, capture_output=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "error")
        self.assertNotIn("Traceback", result.stdout)

    def test_unknown_fields_rejected(self):
        data = json.loads((ROOT / "examples/plugin-input.json").read_text(encoding="utf-8"))
        data["unexpected"] = "value"
        with self.assertRaises(Exception): run(data)

if __name__ == "__main__": unittest.main()
