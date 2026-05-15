from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json
import urllib.request
import io
from pypdf import PdfReader

BASE_URL = "https://examinationboard.aku.edu/about-us/SyllabiList/"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters from the URL
            query = parse_qs(urlparse(self.path).query)
            subject = query.get("subject", [None])[0]
            grade = query.get("grade", [None])[0]

            if not subject or not grade:
                self.send_error_response(400, "Both 'subject' and 'grade' parameters are required.")
                return

            # Construct the PDF filename — AKU-EB pattern: "Physics SSC I Syllabus 2025.pdf"
            filename = f"{subject} {grade} Syllabus 2025.pdf"
            pdf_url = BASE_URL + quote(filename)

            # Download the PDF
            req = urllib.request.Request(
                pdf_url,
                headers={"User-Agent": "Mozilla/5.0 (curriculum-fetcher)"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                pdf_bytes = response.read()

            # Extract text from the PDF
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text() + "\n\n"

            # Return JSON
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_payload = {
                "subject": subject,
                "grade": grade,
                "source_url": pdf_url,
                "content": text_content.strip()
            }
            self.wfile.write(json.dumps(response_payload).encode())

        except urllib.error.HTTPError as e:
            self.send_error_response(404, f"Syllabus not found at AKU-EB: {e}")
        except Exception as e:
            self.send_error_response(500, f"Server error: {str(e)}")

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
