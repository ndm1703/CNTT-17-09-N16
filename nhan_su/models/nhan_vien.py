from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách lịch sử công tác")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách chứng chỉ bằng cấp")
    hop_dong_ids = fields.One2many(
        "hop_dong_nhan_vien",
        inverse_name="nhan_vien_id",
        string="Hợp đồng",
    )
    bang_luong_ids = fields.One2many(
        "bang_luong_nhan_vien",
        inverse_name="nhan_vien_id",
        string="Bảng lương",
    )
    nghi_phep_ids = fields.One2many(
        "nghi_phep_nhan_vien",
        inverse_name="nhan_vien_id",
        string="Nghỉ phép",
    )
    cham_cong_ids = fields.One2many(
        "cham_cong_nhan_vien",
        inverse_name="nhan_vien_id",
        string="Chấm công",
    )
    so_ngay_nghi_khong_phep_thang = fields.Integer(
        "Số ngày nghỉ không phép tháng này",
        compute="_compute_cham_cong_tong_hop",
    )
    so_ngay_cong_thang = fields.Integer(
        "Số ngày công tháng này",
        compute="_compute_cham_cong_tong_hop",
    )
    so_nguoi_bang_tuoi = fields.Integer(
    string="Số người bằng tuổi",
    compute="_compute_so_nguoi_bang_tuoi",
    store=True
)
    
    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['nhan_vien'].search(
                    [
                        ('tuoi', '=', record.tuoi),
                        ('ma_dinh_danh', '!=', record.ma_dinh_danh)
                    ]
                )
                record.so_nguoi_bang_tuoi = len(records)
    _sql_constrains = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    @api.depends("cham_cong_ids.trang_thai", "cham_cong_ids.ngay_cham_cong")
    def _compute_cham_cong_tong_hop(self):
        today = fields.Date.context_today(self)
        for record in self:
            current_month_records = record.cham_cong_ids.filtered(
                lambda item: item.ngay_cham_cong and item.ngay_cham_cong.year == today.year and item.ngay_cham_cong.month == today.month
            )
            record.so_ngay_nghi_khong_phep_thang = len(
                current_month_records.filtered(lambda item: item.trang_thai == "nghi_khong_phep")
            )
            record.so_ngay_cong_thang = len(
                current_month_records.filtered(lambda item: item.trang_thai in ("co_mat", "di_muon", "cong_tac"))
            )

    @api.model
    def _generate_unique_ma_dinh_danh(self, ho_ten_dem, ten):
        ho_ten_dem = (ho_ten_dem or "").strip()
        ten = (ten or "").strip()
        chu_cai_dau = "".join(tu[0] for tu in ho_ten_dem.lower().split() if tu)
        base_code = (ten.lower() + chu_cai_dau) or "nhanvien"
        ma_dinh_danh = base_code
        index = 1
        while self.search_count([("ma_dinh_danh", "=", ma_dinh_danh)]):
            ma_dinh_danh = f"{base_code}{index}"
            index += 1
        return ma_dinh_danh

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
    
    
    
                
    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ma_dinh_danh = self._generate_unique_ma_dinh_danh(record.ho_ten_dem, record.ten)
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                year_now = date.today().year
                record.tuoi = year_now - record.ngay_sinh.year

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_dinh_danh"):
                ho_ten_dem = vals.get("ho_ten_dem") or ""
                ten = vals.get("ten") or ""
                vals["ma_dinh_danh"] = self._generate_unique_ma_dinh_danh(ho_ten_dem, ten)
        return super().create(vals_list)

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.tuoi in (False, None):
                continue
            if record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        current_year = today.year
        history_model = self.env["lich_su_cong_tac"]
        certificate_model = self.env["danh_sach_chung_chi_bang_cap"]
        reward_model = self.env["khen_thuong_xu_phat"]
        department_model = self.env["don_vi"]
        position_model = self.env["chuc_vu"]
        contract_model = self.env["hop_dong_nhan_vien"]
        payroll_model = self.env["bang_luong_nhan_vien"]
        leave_model = self.env["nghi_phep_nhan_vien"]
        attendance_model = self.env["cham_cong_nhan_vien"]

        employees = self.search([])
        total_employees = len(employees)

        active_histories = history_model.search([("trang_thai", "=", "dang_cong_tac")])
        inactive_histories = history_model.search([("trang_thai", "=", "da_nghi")])
        active_employee_ids = set(active_histories.mapped("nhan_vien_id").ids)
        inactive_employee_ids = set(inactive_histories.mapped("nhan_vien_id").ids)

        valid_certificates = certificate_model.search_count([("trang_thai", "=", "con_han")])
        expired_certificates = certificate_model.search_count([("trang_thai", "=", "het_han")])
        total_departments = department_model.search_count([])
        active_contracts = contract_model.search_count([("trang_thai", "=", "hieu_luc")])
        expiring_contracts = contract_model.search_count([("trang_thai", "=", "sap_het_han")])
        current_month = str(today.month)
        current_month_payrolls = payroll_model.search(
            [("thang", "=", current_month), ("nam", "=", current_year)]
        )
        total_payroll_amount = sum(current_month_payrolls.mapped("tong_luong"))
        leave_pending_count = leave_model.search_count([("trang_thai", "=", "cho_duyet")])
        leave_approved_count = leave_model.search_count([("trang_thai", "=", "da_duyet")])
        leave_rejected_count = leave_model.search_count([("trang_thai", "=", "tu_choi")])
        unauthorized_leave_count = attendance_model.search_count(
            [
                ("trang_thai", "=", "nghi_khong_phep"),
                ("ngay_cham_cong", ">=", f"{current_year}-{today.month:02d}-01"),
                ("ngay_cham_cong", "<=", fields.Date.to_string(today)),
            ]
        )

        reward_records = reward_model.search([])
        reward_count = len(reward_records.filtered(lambda rec: rec.loai == "khen_thuong"))
        discipline_count = len(reward_records.filtered(lambda rec: rec.loai == "xu_phat"))
        reward_amount = sum(reward_records.filtered(lambda rec: rec.loai == "khen_thuong").mapped("so_tien"))
        discipline_amount = sum(reward_records.filtered(lambda rec: rec.loai == "xu_phat").mapped("so_tien"))

        department_chart = []
        for department in department_model.search([], order="so_luong_nhan_vien desc, ten_don_vi asc"):
            department_chart.append(
                {
                    "label": department.ten_don_vi,
                    "value": department.so_luong_nhan_vien,
                }
            )

        hiring_month_map = {month: 0 for month in range(1, 13)}
        for history in history_model.search(
            [
                ("ngay_bat_dau", ">=", "%s-01-01" % current_year),
                ("ngay_bat_dau", "<=", "%s-12-31" % current_year),
            ]
        ):
            if history.ngay_bat_dau:
                hiring_month_map[history.ngay_bat_dau.month] += 1

        age_ranges = [
            ("Dưới 25", lambda age: age < 25),
            ("25 - 30", lambda age: 25 <= age <= 30),
            ("31 - 35", lambda age: 31 <= age <= 35),
            ("36 - 40", lambda age: 36 <= age <= 40),
            ("Trên 40", lambda age: age > 40),
        ]
        age_chart = []
        for label, matcher in age_ranges:
            count = 0
            for employee in employees:
                if employee.tuoi and matcher(employee.tuoi):
                    count += 1
            age_chart.append({"label": label, "value": count})

        reward_chart = [
            {"label": "Khen thưởng", "value": reward_count},
            {"label": "Xử phạt", "value": discipline_count},
        ]

        average_position_salary = 0.0
        positions = position_model.search([])
        if positions:
            average_position_salary = sum(positions.mapped("muc_luong_co_ban")) / len(positions)

        return {
            "title": "Tổng quan Nhân sự",
            "current_year": current_year,
            "cards": [
                {
                    "label": "Tổng số nhân viên",
                    "value": total_employees,
                    "theme": "blue",
                    "action_xmlid": "nhan_su.action_nhan_vien",
                },
                {
                    "label": "Đang làm việc",
                    "value": len(active_employee_ids),
                    "theme": "green",
                    "action_xmlid": "nhan_su.action_lich_su_cong_tac",
                },
                {
                    "label": "Hợp đồng hiệu lực",
                    "value": active_contracts,
                    "theme": "cyan",
                    "action_xmlid": "nhan_su.action_hop_dong_nhan_vien",
                },
                {
                    "label": "Bảng lương tháng này",
                    "value": len(current_month_payrolls),
                    "theme": "amber",
                    "action_xmlid": "nhan_su.action_bang_luong_nhan_vien",
                },
                {
                    "label": "Nghỉ phép chờ duyệt",
                    "value": leave_pending_count,
                    "theme": "red",
                    "action_xmlid": "nhan_su.action_nghi_phep_nhan_vien",
                },
                {
                    "label": "Nghỉ không phép",
                    "value": unauthorized_leave_count,
                    "theme": "red",
                    "action_xmlid": "nhan_su.action_cham_cong_nhan_vien",
                },
            ],
            "summary_sections": [
                {
                    "title": "Thống kê vị trí & lương cơ bản",
                    "theme": "slate",
                    "items": [
                        {
                            "label": "Tổng chi lương tháng",
                            "value": "{:,.0f} VND".format(total_payroll_amount).replace(",", "."),
                        },
                        {
                            "label": "Lương cơ bản TB",
                            "value": "{:,.0f} VND".format(average_position_salary).replace(",", "."),
                        },
                    ],
                },
                {
                    "title": "Hợp đồng & phát triển",
                    "theme": "teal",
                    "items": [
                        {
                            "label": "Sắp hết hạn",
                            "value": expiring_contracts,
                        },
                        {
                            "label": "CC hết hạn",
                            "value": expired_certificates,
                        },
                        {
                            "label": "Nghỉ đã duyệt",
                            "value": leave_approved_count,
                        },
                        {
                            "label": "Nghỉ bị từ chối",
                            "value": leave_rejected_count,
                        },
                        {
                            "label": "Nghỉ không phép",
                            "value": unauthorized_leave_count,
                        },
                    ],
                },
            ],
            "charts": {
                "department": department_chart,
                "hiring_trend": [
                    {
                        "label": "Tháng %s" % month,
                        "value": hiring_month_map[month],
                    }
                    for month in range(1, 13)
                ],
                "age_distribution": age_chart,
                "reward_ratio": reward_chart,
            },
            "highlights": [
                {
                    "label": "Tổng tiền khen thưởng",
                    "value": "{:,.0f} VND".format(reward_amount).replace(",", "."),
                },
                {
                    "label": "Tổng tiền xử phạt",
                    "value": "{:,.0f} VND".format(discipline_amount).replace(",", "."),
                },
            ],
            "shortcuts": [
                {
                    "label": "Thông tin nhân viên",
                    "action_xmlid": "nhan_su.action_nhan_vien",
                },
                {
                    "label": "Phòng ban",
                    "action_xmlid": "nhan_su.action_don_vi",
                },
                {
                    "label": "Đào tạo - phát triển",
                    "action_xmlid": "nhan_su.action_danh_sach_chung_chi_bang_cap",
                },
                {
                    "label": "Hợp đồng nhân viên",
                    "action_xmlid": "nhan_su.action_hop_dong_nhan_vien",
                },
                {
                    "label": "Lương nhân viên",
                    "action_xmlid": "nhan_su.action_bang_luong_nhan_vien",
                },
                {
                    "label": "Nghỉ phép",
                    "action_xmlid": "nhan_su.action_nghi_phep_nhan_vien",
                },
                {
                    "label": "Chấm công",
                    "action_xmlid": "nhan_su.action_cham_cong_nhan_vien",
                },
                {
                    "label": "Ứng viên",
                    "action_xmlid": "hr_recruitment.crm_case_categ0_act_job",
                },
                {
                    "label": "Khen thưởng/Xử phạt",
                    "action_xmlid": "nhan_su.action_khen_thuong_xu_phat",
                },
            ],
        }


# extend hr.employee to link work history entries
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    work_history_ids = fields.One2many(
        'hr.work.history', 'employee_id',
        string='Work History'
    )
