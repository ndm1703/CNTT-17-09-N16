import base64
import io
import re
import unicodedata

from odoo import api, fields, models
from odoo.exceptions import UserError


CURATED_KEYWORDS = {
    "odoo": ["odoo", "open erp", "openerp"],
    "python": ["python"],
    "sql": ["sql", "postgresql", "mysql", "database"],
    "excel": ["excel", "spreadsheet"],
    "powerbi": ["power bi", "powerbi", "bi"],
    "erp": ["erp"],
    "crm": ["crm"],
    "sales": ["sales", "bán hàng", "kinh doanh", "tư vấn bán hàng", "telesales"],
    "marketing": ["marketing", "digital marketing", "content", "seo"],
    "recruitment": ["recruitment", "tuyển dụng", "talent acquisition"],
    "hr": ["human resources", "hr", "nhân sự", "c&b"],
    "accounting": ["accounting", "kế toán", "finance", "tài chính"],
    "english": ["english", "tiếng anh", "toeic", "ielts"],
    "giao_tiep": ["giao tiếp", "communication", "communicate"],
    "lam_viec_nhom": ["làm việc nhóm", "teamwork", "team work", "collaboration"],
    "quan_ly_du_an": ["quản lý dự án", "project management", "project manager"],
    "phan_tich_du_lieu": ["phân tích dữ liệu", "data analysis", "data analyst", "analytics"],
    "cham_soc_khach_hang": ["chăm sóc khách hàng", "customer service", "customer care", "client service"],
    "javascript": ["javascript", "js", "nodejs", "node.js"],
    "java": ["java"],
    "php": ["php"],
    "react": ["react", "reactjs", "react.js"],
    "frontend": ["frontend", "front end", "html", "css", "ui"],
    "backend": ["backend", "back end", "api", "server"],
    "tester": ["tester", "testing", "qa", "quality assurance"],
    "business_analyst": ["business analyst", "ba", "phân tích nghiệp vụ"],
}


def _html_to_text(value):
    plain_text = re.sub(r"<[^>]+>", " ", value or "")
    plain_text = plain_text.replace("&nbsp;", " ")
    return _clean_extracted_text(plain_text)


def _normalize_tokens(text):
    if not text:
        return []
    normalized = unicodedata.normalize("NFC", text)
    cleaned = re.sub(r"[^0-9a-zA-ZÀ-ỹ\s]", " ", normalized.lower())
    tokens = [token.strip() for token in cleaned.split() if len(token.strip()) >= 3]
    stopwords = {
        "và", "các", "cho", "với", "của", "the", "and", "hoặc", "trong",
        "kinh", "nghiệm", "ứng", "viên", "công", "việc", "nhân", "sự",
        "mục", "tiêu", "thông", "tin", "liên", "hệ", "địa", "chỉ",
        "điện", "thoại", "email", "họ", "tên", "trình", "độ", "kỹ",
        "năng", "dự", "án", "học", "vấn", "bản", "thân",
        "after", "animate", "answer", "any", "appropriate", "assistance",
        "become", "being", "from", "into", "about", "able", "ability",
        "their", "there", "these", "those", "would", "could", "should",
        "have", "has", "had", "were", "was", "your", "yours", "them",
        "they", "will", "shall", "this", "that", "with", "for", "you",
        "our", "ours", "his", "her", "hers", "him", "its", "it's",
        "job", "jobs", "role", "position", "trainee", "department",
        "better", "books", "brings", "cases", "class", "clients",
        "commercial", "configuration", "functional", "responsible",
        "responsibilities", "requirements", "candidate", "candidates",
        "working", "support", "develop", "developer", "applications",
        "software", "system", "systems", "business", "professional",
        "knowledge", "skills", "experience", "years", "year",
        "ability", "good", "well", "using", "used", "user",
    }
    synonyms = {
        "giao_tiep": ["giao", "tiếp", "giaotiep"],
        "lam_viec_nhom": ["nhóm", "teamwork"],
        "quan_ly_du_an": ["quản", "lý", "dự", "án", "project", "management"],
        "phan_tich_du_lieu": ["phân", "tích", "dữ", "liệu", "data", "analysis"],
        "cham_soc_khach_hang": ["chăm", "sóc", "khách", "hàng", "customer", "service"],
    }
    normalized_tokens = [token for token in tokens if token not in stopwords]
    expanded_tokens = set(normalized_tokens)
    joined_text = " ".join(normalized_tokens)
    for alias, words in synonyms.items():
        if all(word in joined_text for word in words[: min(2, len(words))]) or any(word in expanded_tokens for word in words):
            expanded_tokens.add(alias)
    return list(expanded_tokens)


def _clean_extracted_text(text):
    normalized = unicodedata.normalize("NFC", text or "")
    normalized = normalized.replace("\xa0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _extract_curated_keywords(text):
    normalized_text = unicodedata.normalize("NFC", (text or "").lower())
    found_keywords = []
    for keyword, patterns in CURATED_KEYWORDS.items():
        if any(pattern in normalized_text for pattern in patterns):
            found_keywords.append(keyword)
    return found_keywords


def _parse_date_string(raw_value):
    cleaned_value = (raw_value or "").strip()
    if not cleaned_value:
        return False
    cleaned_value = re.sub(r"[^\d/.-]", "", cleaned_value)
    if not cleaned_value:
        return False

    for separator in ("/", "-", "."):
        if separator in cleaned_value:
            parts = [part for part in cleaned_value.split(separator) if part]
            if len(parts) != 3:
                continue
            try:
                if len(parts[0]) == 4:
                    year, month, day = [int(part) for part in parts]
                else:
                    day, month, year = [int(part) for part in parts]
                if year < 1900 or year > 2100:
                    continue
                return fields.Date.to_string(fields.Date.to_date(f"{year:04d}-{month:02d}-{day:02d}"))
            except Exception:
                continue
    return False


class HrJob(models.Model):
    _inherit = "hr.job"

    don_vi_id = fields.Many2one(
        "don_vi",
        string="Đơn vị nhân sự",
        compute="_compute_don_vi_id",
        inverse="_inverse_don_vi_id",
        store=True,
        readonly=False,
    )
    ai_tieu_chi_tuyen_dung = fields.Text("Tiêu chí AI quét")

    @api.depends("department_id", "department_id.don_vi_id")
    def _compute_don_vi_id(self):
        for record in self:
            record.don_vi_id = record.department_id.don_vi_id

    def _inverse_don_vi_id(self):
        for record in self:
            if record.don_vi_id and record.don_vi_id.hr_department_id:
                record.department_id = record.don_vi_id.hr_department_id

    @api.onchange("department_id")
    def _onchange_department_id(self):
        for record in self:
            if record.department_id and record.department_id.don_vi_id:
                record.don_vi_id = record.department_id.don_vi_id

    @api.onchange("don_vi_id")
    def _onchange_don_vi_id(self):
        for record in self:
            if record.don_vi_id and record.don_vi_id.hr_department_id:
                record.department_id = record.don_vi_id.hr_department_id

    def _extract_ai_criteria_from_description(self):
        self.ensure_one()
        description_text = _html_to_text(self.description)
        source_text = " ".join(
            part
            for part in (
                self.name,
                self.department_id.name,
                description_text,
            )
            if part
        )
        curated_keywords = _extract_curated_keywords(source_text)
        if curated_keywords:
            return ", ".join(curated_keywords[:15])

        fallback_tokens = []
        for token in _normalize_tokens(" ".join(part for part in (self.name, self.department_id.name) if part)):
            if token not in fallback_tokens:
                fallback_tokens.append(token)
        return ", ".join(fallback_tokens[:8])

    def action_goi_y_tieu_chi_ai(self):
        for record in self:
            suggestion = record._extract_ai_criteria_from_description()
            if suggestion:
                record.ai_tieu_chi_tuyen_dung = suggestion


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    don_vi_id = fields.Many2one(
        "don_vi",
        string="Đơn vị nhân sự",
        compute="_compute_don_vi_id",
        inverse="_inverse_don_vi_id",
        store=True,
        readonly=False,
    )
    nhan_vien_id = fields.Many2one("nhan_vien", string="Nhân viên liên kết", copy=False, readonly=True)
    ngay_sinh = fields.Date("Ngày sinh", copy=False)
    cv_file = fields.Binary("CV", attachment=True, copy=False)
    cv_filename = fields.Char("Tên file CV", copy=False)
    cv_extracted_text = fields.Text("Nội dung CV trích xuất", readonly=True, copy=False)
    ai_match_score = fields.Float("Điểm phù hợp AI", readonly=True, copy=False)
    ai_fit_level = fields.Selection(
        [
            ("low", "Thấp"),
            ("medium", "Trung bình"),
            ("high", "Cao"),
        ],
        string="Mức độ phù hợp",
        readonly=True,
        copy=False,
    )
    ai_diem_manh = fields.Text("Điểm mạnh AI", readonly=True, copy=False)
    ai_diem_yeu = fields.Text("Điểm yếu AI", readonly=True, copy=False)
    ai_scan_summary = fields.Text("Kết quả AI quét", readonly=True, copy=False)
    ai_last_scan = fields.Datetime("Lần quét gần nhất", readonly=True, copy=False)

    @api.depends(
        "job_id",
        "job_id.don_vi_id",
        "department_id",
        "department_id.don_vi_id",
    )
    def _compute_don_vi_id(self):
        for record in self:
            record.don_vi_id = record.job_id.don_vi_id or record.department_id.don_vi_id

    def _inverse_don_vi_id(self):
        for record in self:
            if record.don_vi_id and record.don_vi_id.hr_department_id:
                record.department_id = record.don_vi_id.hr_department_id

    @api.onchange("job_id")
    def _onchange_job_id_sync_department(self):
        for record in self:
            if record.job_id:
                record.department_id = record.job_id.department_id
                record.don_vi_id = record.job_id.don_vi_id

    @api.onchange("department_id")
    def _onchange_department_id_sync_don_vi(self):
        for record in self:
            if record.department_id and record.department_id.don_vi_id:
                record.don_vi_id = record.department_id.don_vi_id

    @api.onchange("don_vi_id")
    def _onchange_don_vi_id_sync_department(self):
        for record in self:
            if record.don_vi_id and record.don_vi_id.hr_department_id:
                record.department_id = record.don_vi_id.hr_department_id

    def _get_job_scan_source(self):
        self.ensure_one()
        description = self.job_id.ai_tieu_chi_tuyen_dung or self.job_id._extract_ai_criteria_from_description() or ""
        parts = [
            self.job_id.name,
            description,
            self.job_id.department_id.name,
        ]
        return " ".join(part for part in parts if part)

    def _get_applicant_scan_source(self):
        self.ensure_one()
        attachment_names = ", ".join(self.attachment_ids.mapped("name"))
        parts = [
            self.name,
            self.partner_name,
            self.email_from,
            self.partner_phone,
            self.partner_mobile,
            self.description,
            self.type_id.name,
            self.cv_filename,
            self.cv_extracted_text,
            attachment_names,
        ]
        return " ".join(part for part in parts if part)

    def _extract_text_from_cv(self):
        self.ensure_one()
        if not self.cv_file or not self.cv_filename:
            return ""

        raw = base64.b64decode(self.cv_file)
        filename = (self.cv_filename or "").lower()

        if filename.endswith(".txt"):
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.decode("latin-1", errors="ignore")

        if filename.endswith(".pdf"):
            try:
                import pdfplumber

                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    return _clean_extracted_text("\n".join((page.extract_text() or "") for page in pdf.pages))
            except Exception:
                try:
                    import PyPDF2

                    reader = PyPDF2.PdfReader(io.BytesIO(raw))
                    return _clean_extracted_text("\n".join((page.extract_text() or "") for page in reader.pages))
                except Exception:
                    return ""

        return ""

    def _extract_candidate_info_from_text(self, text):
        cleaned_text = _clean_extracted_text(text)
        lines = [line.strip(" -:\t") for line in cleaned_text.splitlines() if line.strip()]
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cleaned_text)
        phone_match = re.search(r"(\+?84|0)(?:[\s\.-]?\d){8,10}", cleaned_text)

        labeled_name_match = re.search(
            r"(họ và tên|họ tên|ứng viên|candidate|full name)\s*[:\-]\s*([^\n]+)",
            cleaned_text,
            re.IGNORECASE,
        )
        birth_match = re.search(
            r"(ngày sinh|ngay sinh|date of birth|birth date|dob)\s*[:\-]?\s*(\d{1,4}[\/\.-]\d{1,2}[\/\.-]\d{1,4})",
            cleaned_text,
            re.IGNORECASE,
        )
        name = labeled_name_match.group(2).strip() if labeled_name_match else ""
        if not name:
            for line in lines[:6]:
                if len(line.split()) < 2 or len(line.split()) > 6:
                    continue
                if any(char.isdigit() for char in line):
                    continue
                lowered = line.lower()
                if any(
                    keyword in lowered
                    for keyword in (
                        "mục tiêu", "kinh nghiệm", "học vấn", "kỹ năng",
                        "thông tin", "liên hệ", "email", "điện thoại", "địa chỉ",
                    )
                ):
                    continue
                name = line
                break

        description_lines = []
        skip_prefixes = (
            "họ và tên", "họ tên", "email", "điện thoại", "số điện thoại",
            "địa chỉ", "ngày sinh", "ứng viên", "candidate", "full name",
        )
        for line in lines:
            lowered = line.lower()
            if any(lowered.startswith(prefix) for prefix in skip_prefixes):
                continue
            description_lines.append(line)
            if len(description_lines) >= 20:
                break

        return {
            "partner_name": name[:128] if name else False,
            "email_from": email_match.group(0) if email_match else False,
            "partner_phone": phone_match.group(0).strip() if phone_match else False,
            "ngay_sinh": _parse_date_string(birth_match.group(2)) if birth_match else False,
            "description": "\n".join(description_lines) if description_lines else False,
            "cv_extracted_text": cleaned_text or False,
        }

    def _apply_cv_autofill(self, force=False):
        for record in self:
            text = record._extract_text_from_cv()
            extracted = record._extract_candidate_info_from_text(text)
            updates = {}
            field_mapping = {
                "partner_name": "partner_name",
                "email_from": "email_from",
                "partner_phone": "partner_phone",
                "ngay_sinh": "ngay_sinh",
                "description": "description",
                "cv_extracted_text": "cv_extracted_text",
            }
            for target_field, extracted_key in field_mapping.items():
                value = extracted.get(extracted_key)
                if not value:
                    continue
                current_value = record[target_field]
                if force or not current_value:
                    updates[target_field] = value

            if extracted.get("partner_name") and (force or not record.name):
                updates["name"] = extracted["partner_name"]

            if updates:
                record.update(updates)

    def _build_ai_scan_result(self):
        self.ensure_one()
        job_tokens = set(_normalize_tokens(self._get_job_scan_source()))
        applicant_tokens = set(_normalize_tokens(self._get_applicant_scan_source()))
        if not self.job_id:
            return {
                "score": 0.0,
                "fit_level": "low",
                "strengths": "Chưa có dữ liệu vị trí tuyển dụng để xác định điểm mạnh.",
                "weaknesses": "Chưa có vị trí tuyển dụng để xác định điểm yếu.",
                "summary": "Chưa có vị trí tuyển dụng để AI quét đối sánh.",
            }
        if not job_tokens:
            return {
                "score": 0.0,
                "fit_level": "low",
                "strengths": "Đã đọc được CV nhưng chưa đủ tiêu chí vị trí để phân tích điểm mạnh.",
                "weaknesses": "Chưa đủ dữ liệu tiêu chí từ vị trí tuyển dụng.",
                "summary": "Chưa đủ dữ liệu để gợi ý tiêu chí AI từ vị trí tuyển dụng. Vui lòng nhập thêm mô tả công việc hoặc tiêu chí AI quét.",
            }
        if not self.cv_extracted_text and not self.description:
            return {
                "score": 0.0,
                "fit_level": "low",
                "strengths": "Chưa đọc được nội dung CV để xác định điểm mạnh.",
                "weaknesses": "Thiếu nội dung CV nên chưa đánh giá được các điểm còn thiếu.",
                "summary": "Chưa đọc được nội dung CV PDF. Vui lòng dùng PDF có text hoặc nhập thêm mô tả ứng viên.",
            }

        matched_tokens = sorted(job_tokens & applicant_tokens)
        missing_tokens = sorted(job_tokens - applicant_tokens)
        score = round((len(matched_tokens) / len(job_tokens)) * 100, 2) if job_tokens else 0.0

        if score >= 70:
            fit_level = "high"
            label = "Phù hợp cao"
        elif score >= 40:
            fit_level = "medium"
            label = "Phù hợp trung bình"
        else:
            fit_level = "low"
            label = "Phù hợp thấp"

        matched_preview = ", ".join(matched_tokens[:8]) if matched_tokens else "Chưa tìm thấy từ khóa phù hợp"
        missing_preview = ", ".join(missing_tokens[:8]) if missing_tokens else "Không có"
        strengths = (
            f"Khớp tốt với các tiêu chí: {matched_preview}."
            if matched_tokens
            else "Chưa thấy kỹ năng hoặc từ khóa nổi bật trùng với yêu cầu vị trí."
        )
        weaknesses = (
            f"Còn thiếu hoặc chưa thể hiện rõ: {missing_preview}."
            if missing_tokens
            else "Chưa thấy điểm yếu rõ ràng theo bộ tiêu chí hiện tại."
        )
        summary = (
            f"{label} ({score}%). "
            f"Khớp: {matched_preview}. "
            f"Còn thiếu: {missing_preview}."
        )
        return {
            "score": score,
            "fit_level": fit_level,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "summary": summary,
        }

    def _split_full_name(self):
        self.ensure_one()
        full_name = (self.partner_name or self.name or "").strip()
        if not full_name:
            raise UserError("Ứng viên chưa có họ tên để tạo hồ sơ nhân viên.")
        name_parts = full_name.split()
        if len(name_parts) == 1:
            return "", name_parts[0]
        return " ".join(name_parts[:-1]), name_parts[-1]

    def _prepare_nhan_vien_vals(self):
        self.ensure_one()
        ho_ten_dem, ten = self._split_full_name()
        return {
            "ho_ten_dem": ho_ten_dem or ten,
            "ten": ten,
            "ngay_sinh": self.ngay_sinh,
            "email": self.email_from,
            "so_dien_thoai": self.partner_phone or self.partner_mobile,
        }

    def _find_matching_chuc_vu(self):
        self.ensure_one()
        domain = []
        if self.don_vi_id:
            domain.append(("don_vi_id", "=", self.don_vi_id.id))
        if self.job_id and self.job_id.name:
            domain.append(("ten_chuc_vu", "ilike", self.job_id.name))
        return self.env["chuc_vu"].search(domain, limit=1) if domain else self.env["chuc_vu"].browse()

    def _ensure_lich_su_cong_tac(self, nhan_vien):
        self.ensure_one()
        start_date = fields.Date.context_today(self)
        chuc_vu = self._find_matching_chuc_vu()
        existing_history = self.env["lich_su_cong_tac"].search(
            [
                ("nhan_vien_id", "=", nhan_vien.id),
                ("ngay_ket_thuc", "=", False),
            ],
            limit=1,
        )
        history_vals = {
            "nhan_vien_id": nhan_vien.id,
            "don_vi_id": self.don_vi_id.id,
            "hr_department_id": self.department_id.id,
            "chuc_vu_id": chuc_vu.id if chuc_vu else False,
            "ngay_bat_dau": start_date,
        }
        if existing_history:
            existing_history.write(history_vals)
            return existing_history
        return self.env["lich_su_cong_tac"].create(history_vals)

    def action_tiep_nhan_nhan_vien(self):
        for record in self:
            if record.nhan_vien_id:
                continue
            if not record.don_vi_id and not record.department_id:
                raise UserError("Vui lòng chọn phòng ban hoặc đơn vị trước khi tiếp nhận thành nhân viên.")
            nhan_vien = record.env["nhan_vien"].create(record._prepare_nhan_vien_vals())
            record._ensure_lich_su_cong_tac(nhan_vien)
            record.nhan_vien_id = nhan_vien.id
        return True

    def action_xem_nhan_vien_lien_ket(self):
        self.ensure_one()
        if not self.nhan_vien_id:
            raise UserError("Ứng viên này chưa được tiếp nhận thành nhân viên.")
        return {
            "type": "ir.actions.act_window",
            "name": "Nhân viên",
            "res_model": "nhan_vien",
            "view_mode": "form",
            "res_id": self.nhan_vien_id.id,
            "target": "current",
        }

    def action_ai_scan_for_job(self):
        for record in self:
            result = record._build_ai_scan_result()
            record.write(
                {
                    "ai_match_score": result["score"],
                    "ai_fit_level": result["fit_level"],
                    "ai_diem_manh": result["strengths"],
                    "ai_diem_yeu": result["weaknesses"],
                    "ai_scan_summary": result["summary"],
                    "ai_last_scan": fields.Datetime.now(),
                }
            )

    @api.onchange("cv_file", "cv_filename")
    def _onchange_cv_file(self):
        self._apply_cv_autofill()

    @api.onchange("job_id", "description", "partner_name", "email_from", "type_id", "cv_extracted_text")
    def _onchange_ai_preview(self):
        for record in self:
            if not record.job_id:
                continue
            result = record._build_ai_scan_result()
            record.ai_match_score = result["score"]
            record.ai_fit_level = result["fit_level"]
            record.ai_diem_manh = result["strengths"]
            record.ai_diem_yeu = result["weaknesses"]
            record.ai_scan_summary = result["summary"]

    @api.model_create_multi
    def create(self, vals_list):
        synced_vals_list = [self._sync_recruitment_department_values(vals) for vals in vals_list]
        records = super().create(synced_vals_list)
        for record in records.filtered(lambda rec: rec.cv_file):
            record._apply_cv_autofill(force=False)
        return records

    def write(self, vals):
        vals = self._sync_recruitment_department_values(vals)
        res = super().write(vals)
        if "cv_file" in vals or "cv_filename" in vals:
            for record in self.filtered(lambda rec: rec.cv_file):
                record._apply_cv_autofill(force=False)
        return res

    @api.model
    def _sync_recruitment_department_values(self, vals):
        synced_vals = dict(vals)
        if synced_vals.get("don_vi_id") and not synced_vals.get("department_id"):
            don_vi = self.env["don_vi"].browse(synced_vals["don_vi_id"])
            if don_vi.hr_department_id:
                synced_vals["department_id"] = don_vi.hr_department_id.id
        elif synced_vals.get("department_id") and not synced_vals.get("don_vi_id"):
            department = self.env["hr.department"].browse(synced_vals["department_id"])
            if department.don_vi_id:
                synced_vals["don_vi_id"] = department.don_vi_id.id
        return synced_vals


class HrDepartment(models.Model):
    _inherit = "hr.department"

    don_vi_id = fields.Many2one("don_vi", string="Đơn vị nhân sự")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_don_vi_links()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_don_vi_links()
        return res

    def _sync_don_vi_links(self):
        for record in self.filtered("don_vi_id"):
            if record.don_vi_id.hr_department_id != record:
                record.don_vi_id.hr_department_id = record.id
