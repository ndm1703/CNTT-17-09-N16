from datetime import datetime
import logging
import zipfile

from odoo import models
import base64
import io
import pdfplumber
import os
import json
import re


class DocumentAIService(models.AbstractModel):
    _name = 'document.ai.service'
    _description = 'Document AI Service'

    DATE_REGEX = r'(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4})'

    def analyze_document(self, file_binary, filename=None):
        """Return metadata extracted from the document."""
        text = self._extract_text(file_binary)
        if not text:
            return {}
        for provider, env_key in (
            (self._analyze_with_openai, 'OPENAI_API_KEY'),
            (self._analyze_with_gemini, 'GOOGLE_API_KEY'),
        ):
            api_key = os.environ.get(env_key)
            if api_key:
                result = provider(text, api_key)
                if result:
                    return result
        return self._basic_analysis(text)

    def _extract_text(self, file_binary):
        if not file_binary:
            return ""
        pdf_bytes = base64.b64decode(file_binary)
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except Exception as exc:
            logging.info("PDF parsing failed, falling back to other formats: %s", exc)
        return self._extract_text_from_docx(pdf_bytes)

    def _extract_text_from_docx(self, pdf_bytes):
        try:
            with zipfile.ZipFile(io.BytesIO(pdf_bytes)) as docx:
                raw = docx.read('word/document.xml').decode('utf-8')
            # strip XML tags
            text = re.sub(r'<[^>]+>', ' ', raw)
            return re.sub(r'\\s+', ' ', text).strip()
        except Exception as exc:
            logging.info("Docx extraction failed: %s", exc)
            return ""

    def _analyze_with_openai(self, text, api_key):
        try:
            import requests
        except ImportError:
            return None

        prompt = f"""Trích xuất thông tin sau từ văn bản dưới dạng JSON:
{{
  "title": "Tên hoặc tiêu đề của văn bản",
  "document_number": "Mã hiệu/ số văn bản nếu có",
  "sender": "Đơn vị/ cá nhân gửi (nếu có)",
  "recipient": "Người hoặc đơn vị nhận",
  "partner": "Đối tác liên quan (nếu có)",
  "due_date": "Ngày hết hạn hoặc ngày văn bản đề cập tới (YYYY-MM-DD hoặc DD/MM/YYYY)",
  "summary": "Đoạn tóm tắt ngắn gọn (tiếng Việt)"
}}

Văn bản:
{text[:2000]}

Trả về JSON hợp lệ, không thêm nội dung khác."""
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json={
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {'role': 'system', 'content': 'You are a Vietnamese document assistant.'},
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0.2,
                    'max_tokens': 500,
                },
                timeout=10,
            )
            if response.status_code == 200:
                payload = response.json()
                content = payload['choices'][0]['message']['content'].strip()
                parsed = json.loads(content)
                for key in ['title', 'document_number', 'sender', 'recipient', 'partner', 'summary']:
                    parsed.setdefault(key, '')
                parsed['due_date'] = self._normalize_date_string(parsed.get('due_date'))
                return parsed
        except Exception:
            pass
        return None

    def _analyze_with_gemini(self, text, api_key):
        try:
            import requests
        except ImportError:
            return None

        prompt = f"""Phân tích văn bản dưới đây và trả về dạng JSON:
{{
  "title": "Tên văn bản",
  "document_number": "Số/ mã văn bản",
  "sender": "Nơi gửi",
  "recipient": "Nơi nhận",
  "partner": "Đối tác",
  "due_date": "Ngày hết hạn (YYYY-MM-DD hoặc DD/MM/YYYY)",
  "summary": "Tóm tắt ngắn"
}}

Nội dung:
{text[:2000]}

Chỉ trả về JSON hợp lệ."""
        try:
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}',
                json={'contents': [{'parts': [{'text': prompt}]}]},
                headers={'Content-Type': 'application/json'},
                timeout=10,
            )
            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                parsed = json.loads(content)
                for key in ['title', 'document_number', 'sender', 'recipient', 'partner', 'summary']:
                    parsed.setdefault(key, '')
                parsed['due_date'] = self._normalize_date_string(parsed.get('due_date'))
                return parsed
        except Exception:
            pass
        return None

    def _basic_analysis(self, text):
        return {
            'title': self._extract_title(text),
            'document_number': self._extract_document_number(text),
            'sender': self._search_label(text, ['Nơi gửi', 'Đơn vị gửi', 'Người ký']),
            'recipient': self._search_label(text, ['Nơi nhận', 'Đơn vị nhận', 'Người nhận']),
            'partner': self._search_label(text, ['Đối tác', 'Đơn vị phối hợp']),
            'due_date': self._extract_due_date(text),
            'summary': self._extract_summary(text),
        }

    def _extract_title(self, text):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:5]:
            if len(line) > 10:
                return line
        return lines[0] if lines else ""

    def _extract_document_number(self, text):
        match = re.search(r'(?:Số văn bản|Số hiệu|Số|Mã số|Mã|Số hiệu văn bản)[:\\s]+([A-Za-z0-9/\\-]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _search_label(self, text, labels):
        for label in labels:
            pattern = rf'{label}[:\\s-]*(.+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).splitlines()[0].strip()
        return ""

    def _extract_due_date(self, text):
        match = re.search(self.DATE_REGEX, text)
        if not match:
            return ""
        return self._normalize_date_string(match.group(1))

    def _extract_summary(self, text):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""
        summary_lines = lines[1:4] if len(lines) > 1 else lines[:1]
        return ' '.join(summary_lines)[:120]

    def _normalize_date_string(self, value):
        if not value:
            return ""
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                parsed = datetime.strptime(value.strip(), fmt)
                return parsed.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        return ""
