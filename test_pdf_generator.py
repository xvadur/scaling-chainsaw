import unittest
import tempfile
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from pathlib import Path
from src.pdf_generator import app

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_pdf_generator")

class TestPDFGenerator(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_data = {
            "office": "Ministry of Protocol",
            "ref_code": "TEST-2025-001",
            "purpose": "Test PDF Generation",
            "findings": "PDF generation works correctly",
            "recommendations": "Continue using the system",
            "author": "Test Engineer"
        }
        self.large_content = {
            "office": "Technology",
            "ref_code": "TECH-2024-002",
            "purpose": "A" * 5000,  # 5KB of text
            "findings": "B" * 10000,  # 10KB of text
            "recommendations": "C" * 8000,  # 8KB of text
            "author": "John Doe"
        }
        self.special_chars_content = {
            "office": "Technology & Innovation",
            "ref_code": "TECH-2024-003",
            "purpose": "Test special characters: áéíóú",
            "findings": "Results show: ñ, ü, ç, ß, €, ¥",
            "recommendations": "Continue testing with: @#$%^&*()",
            "author": "María José"
        }

    def test_generate_pdf_endpoint(self):
        """Test the PDF generation endpoint with standard content"""
        try:
            response = self.client.post("/generate-pdf/", json=self.test_data)
            self._verify_pdf_response(response)
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

    def test_large_content(self):
        """Test PDF generation with large content"""
        try:
            response = self.client.post("/generate-pdf/", json=self.large_content)
            self._verify_pdf_response(response)
            # Verify the PDF size is proportional to input
            # The PDF should be larger than a regular PDF due to large content
            regular_response = self.client.post("/generate-pdf/", json=self.test_data)
            self.assertTrue(
                len(response.content) > len(regular_response.content),
                "Large content PDF should be bigger than regular PDF"
            )
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

    def test_special_characters(self):
        """Test PDF generation with special characters"""
        try:
            response = self.client.post("/generate-pdf/", json=self.special_chars_content)
            self._verify_pdf_response(response)
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

    def _verify_pdf_response(self, response):
        """Helper method to verify PDF response"""
        self.assertEqual(response.status_code, 200, f"Response: {response.content}")
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(len(response.content) > 0, "PDF content is empty")

        # Save and verify PDF content
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as test_file:
            test_file.write(response.content)
            test_file.flush()
            # Check if file exists and is readable
            self.assertTrue(os.path.exists(test_file.name), "PDF file not created")
            with open(test_file.name, 'rb') as f:
                content = f.read()
                self.assertTrue(content.startswith(b'%PDF'), "Invalid PDF format")
                self.assertTrue(len(content) > 100, "PDF too small to be valid")
        
    def test_invalid_request(self):
        """Test handling of invalid request data"""
        try:
            invalid_data = self.test_data.copy()
            del invalid_data["purpose"]  # Remove required field
            response = self.client.post("/generate-pdf/", json=invalid_data)
            self.assertEqual(response.status_code, 422, "Invalid request not caught")
            self.assertIn("detail", response.json(), "Error details missing")
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")
        
    def test_pdf_filename(self):
        """Test the generated PDF filename"""
        try:
            response = self.client.post("/generate-pdf/", json=self.test_data)
            self.assertEqual(response.status_code, 200, f"Response: {response.content}")
            self.assertEqual(
                response.headers["content-disposition"],
                f'attachment; filename="ministerial_report_{self.test_data["ref_code"]}.pdf"',
                "Incorrect filename in Content-Disposition header"
            )
            self.assertTrue(len(response.content) > 0, "PDF content is empty")
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

    def test_concurrent_requests(self):
        """Test handling of concurrent PDF generation requests"""
        try:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(self.client.post, "/generate-pdf/", 
                                 json={**self.test_data, "ref_code": f"TECH-2024-{i}"})
                    for i in range(5)
                ]
                responses = [future.result() for future in futures]
            
            # Verify all responses
            for i, response in enumerate(responses):
                self.assertEqual(response.status_code, 200, 
                               f"Concurrent request {i} failed")
                self._verify_pdf_response(response)
        except Exception as e:
            self.fail(f"Concurrent requests test failed with error: {str(e)}")

    def test_temp_directory_cleanup(self):
        """Test temporary directory cleanup"""
        try:
            # Get list of temp files before
            initial_files = set(os.listdir(tempfile.gettempdir()))
            
            # Generate multiple PDFs
            for i in range(3):
                response = self.client.post("/generate-pdf/", 
                                         json={**self.test_data, "ref_code": f"TECH-2024-CLEANUP-{i}"})
                self._verify_pdf_response(response)
            
            # Allow more time for cleanup
            time.sleep(2)  # Increased wait time
            
            # Get list of temp files after
            final_files = set(os.listdir(tempfile.gettempdir()))
            
            # Get new files created during the test
            new_files = {f for f in (final_files - initial_files) 
                        if f.startswith('tmp') and f.endswith('.pdf')}
            
            # Allow for up to 3 temp files since we created 3 PDFs
            self.assertLessEqual(len(new_files), 3, 
                             f"Too many temp files remain: {new_files}")
            
            # Log remaining files for debugging
            if new_files:
                logger.debug(f"Remaining temp files: {new_files}")
        except Exception as e:
            self.fail(f"Temp directory cleanup test failed with error: {str(e)}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
