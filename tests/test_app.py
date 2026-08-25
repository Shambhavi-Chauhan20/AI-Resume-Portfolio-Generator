import unittest
import os
import io
import shutil
import sys
from unittest.mock import patch

# ── Make backend importable from tests/ ──────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app import app
import gemini_client

class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Skip live API tests gracefully if the key is not configured
        if not os.getenv("GEMINI_API_KEY"):
            raise unittest.SkipTest("GEMINI_API_KEY not set — skipping live API tests")  # Fix #8

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_case_1_no_file(self):
        print("\n[Test 1] No file uploaded case...")
        response = self.client.post('/generate')
        print(f"  -> Status: {response.status_code}, Response: {response.get_json()}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No resume uploaded", response.get_json()['error'])

        # Empty filename
        response = self.client.post('/generate', data={'resume': (io.BytesIO(b""), "")})
        self.assertEqual(response.status_code, 400)

    def test_case_2_short_resume(self):
        print("\n[Test 2] Short resume (<50 characters) case...")
        short_text = b"Too short resume text."
        response = self.client.post('/generate', data={'resume': (io.BytesIO(short_text), "resume.txt")})
        print(f"  -> Status: {response.status_code}, Response: {response.get_json()}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Resume content too short", response.get_json()['error'])  # Fix #9: correct message

    def test_case_4_live_gemini_success(self):
        print("\n[Test 4] Live Gemini API success case...")
        resume_text = (
            b"John Doe\nSoftware Engineer with 5 years of experience in Python, "
            b"Flask, and Cloud architectures. Developed multiple web applications "
            b"and integrated AI APIs to improve automation by 40%."
        )
        response = self.client.post('/generate', data={'resume': (io.BytesIO(resume_text), "resume.txt")})
        print(f"  -> Status: {response.status_code}")
        print(f"  -> Response Preview: {response.data[:150].decode()}...")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"<!DOCTYPE html>" in response.data or b"<html" in response.data)

    def test_case_5_forced_gemini_failure(self):
        print("\n[Test 5] Forced Gemini API failure case...")
        # Temporarily mock the Gemini client to use an invalid API key
        original_client = gemini_client._client
        from google import genai
        gemini_client._client = genai.Client(api_key="INVALID_KEY")
        
        resume_text = (
            b"John Doe\nSoftware Engineer with 5 years of experience in Python, "
            b"Flask, and Cloud architectures. Developed multiple web applications "
            b"and integrated AI APIs to improve automation by 40%."
        )
        try:
            response = self.client.post('/generate', data={'resume': (io.BytesIO(resume_text), "resume.txt")})
            print(f"  -> Status: {response.status_code}, Response: {response.get_json()}")
            self.assertEqual(response.status_code, 502)
            self.assertIn("Gemini request failed", response.get_json()['error'])
        finally:
            # Restore the client
            gemini_client._client = original_client

    def test_case_6_invalid_json_response(self):
        print("\n[Test 6] Invalid JSON response from Gemini case...")
        resume_text = (
            b"John Doe\nSoftware Engineer with 5 years of experience in Python, "
            b"Flask, and Cloud architectures. Developed multiple web applications "
            b"and integrated AI APIs to improve automation by 40%."
        )
        # Mock get_gemini_response to return garbage (not valid JSON).
        # Must patch 'app.get_gemini_response' because app.py imports the
        # function directly with 'from gemini_client import get_gemini_response'.
        with patch("app.get_gemini_response", return_value="This is not JSON at all!"):
            response = self.client.post(
                "/generate",
                data={"resume": (io.BytesIO(resume_text), "resume.txt")},
            )
        print(f"  -> Status: {response.status_code}, Response: {response.get_json()}")
        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to build portfolio", response.get_json()["error"])

def run_test_case_3_missing_api_key():
    print("\n[Test 3] Missing API key startup failure case...")
    backend_dir = _BACKEND           # fixed: tests/ moved, backend/ didn't
    workspace_dir = _ROOT
    env_path = os.path.join(workspace_dir, ".env")
    env_tmp_path = os.path.join(workspace_dir, ".env.tmp")

    env_exists = os.path.exists(env_path)
    if env_exists:
        shutil.move(env_path, env_tmp_path)

    try:
        import subprocess
        sub_env = os.environ.copy()
        if "GEMINI_API_KEY" in sub_env:
            del sub_env["GEMINI_API_KEY"]
        
        result = subprocess.run(
            [sys.executable, "-c", "import gemini_client"],
            cwd=backend_dir,
            env=sub_env,
            capture_output=True,
            text=True
        )
        
        if "RuntimeError: GEMINI_API_KEY is missing" in result.stderr or "RuntimeError: GEMINI_API_KEY is missing" in result.stdout:
            print("  -> Status: RuntimeError raised correctly at startup!")
            return True
        else:
            print("  -> Status: FAILED. App did not raise RuntimeError on missing API key.")
            return False
    finally:
        if env_exists:
            shutil.move(env_tmp_path, env_path)

if __name__ == '__main__':
    # First run the startup test
    tc3_passed = run_test_case_3_missing_api_key()
    
    # Run the rest of the unit tests
    print("\n--- Running Remaining Unit Tests ---")
    suite = unittest.TestLoader().loadTestsFromTestCase(FlaskAppTests)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    if result.wasSuccessful() and tc3_passed:
        print("\nALL 5 TEST CASES PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\nSOME TEST CASES FAILED!")
        sys.exit(1)
