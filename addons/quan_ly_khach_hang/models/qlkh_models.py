from datetime import date

from odoo import api, fields, models


class QLKHKhachHang(models.Model):
    _name = "qlkh.khach_hang"
    _description = "Khách hàng"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "ten_khach_hang"
    _order = "ma_khach_hang asc"

    ma_khach_hang = fields.Char("Mã khách hàng", required=True, copy=False, default="New")
    ten_khach_hang = fields.Char("Tên khách hàng", required=True, tracking=True)
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    dia_chi = fields.Char("Địa chỉ")
    loai_khach_hang = fields.Selection(
        [("ca_nhan", "Cá nhân"), ("cong_ty", "Công ty")],
        string="Loại khách hàng",
        required=True,
        default="ca_nhan",
        tracking=True,
    )
    muc_thu_nhap = fields.Selection(
        [
            ("0_20", "0-20 triệu/tháng"),
            ("20_50", "20-50 triệu/tháng"),
            ("50_70", "50-70 triệu/tháng"),
            ("70_100", "70-100 triệu/tháng"),
            ("100_plus", "100 triệu trở lên"),
        ],
        string="Mức thu nhập",
    )
    gioi_tinh = fields.Selection(
        [("nu", "Nữ"), ("nam", "Nam"), ("khac", "Khác")],
        string="Giới tính",
    )
    ngay_sinh = fields.Date("Ngày sinh")
    nhom_do_tuoi = fields.Selection(
        [
            ("0_20", "0-20 tuổi"),
            ("20_30", "20-30 tuổi"),
            ("30_40", "30-40 tuổi"),
            ("40_50", "40-50 tuổi"),
            ("50_plus", "Trên 50 tuổi"),
        ],
        string="Nhóm độ tuổi",
        compute="_compute_nhom_do_tuoi",
        store=True,
    )
    ten_cong_ty = fields.Char("Tên công ty")
    trang_thai = fields.Selection(
        [("moi", "Mới"), ("dang_hoat_dong", "Đang hoạt động"), ("tam_dung", "Tạm dừng")],
        string="Trạng thái",
        default="moi",
        tracking=True,
    )
    tong_so_don_hang = fields.Integer("Tổng số đơn hàng", compute="_compute_tong_so_don_hang", store=True)
    tong_giao_dich = fields.Float("Tổng giao dịch", compute="_compute_tong_giao_dich", store=True)
    ghi_chu_tong_quan = fields.Text("Ghi chú")

    co_hoi_ids = fields.One2many("qlkh.co_hoi", "khach_hang_id", string="Cơ hội")
    tuong_tac_ids = fields.One2many("qlkh.tuong_tac", "khach_hang_id", string="Tương tác")
    hop_dong_ids = fields.One2many("qlkh.hop_dong", "khach_hang_id", string="Hợp đồng")
    giao_dich_ids = fields.One2many("qlkh.giao_dich", "khach_hang_id", string="Lịch sử giao dịch")
    ghi_chu_ids = fields.One2many("qlkh.ghi_chu", "khach_hang_id", string="Ghi chú")
    phan_hoi_ids = fields.One2many("qlkh.phan_hoi", "khach_hang_id", string="Phản hồi")
    nhiem_vu_ids = fields.One2many("qlkh.nhiem_vu", "khach_hang_id", string="Nhiệm vụ")
    marketing_ids = fields.One2many("qlkh.marketing", "khach_hang_id", string="Marketing")

    _sql_constraints = [
        ("ma_khach_hang_unique", "unique(ma_khach_hang)", "Mã khách hàng phải là duy nhất."),
    ]

    @api.depends("ngay_sinh")
    def _compute_nhom_do_tuoi(self):
        current_year = date.today().year
        for record in self:
            record.nhom_do_tuoi = False
            if not record.ngay_sinh:
                continue
            age = current_year - record.ngay_sinh.year
            if age <= 20:
                record.nhom_do_tuoi = "0_20"
            elif age <= 30:
                record.nhom_do_tuoi = "20_30"
            elif age <= 40:
                record.nhom_do_tuoi = "30_40"
            elif age <= 50:
                record.nhom_do_tuoi = "40_50"
            else:
                record.nhom_do_tuoi = "50_plus"

    @api.depends("giao_dich_ids")
    def _compute_tong_so_don_hang(self):
        for record in self:
            record.tong_so_don_hang = len(record.giao_dich_ids)

    @api.depends("giao_dich_ids.gia_tri")
    def _compute_tong_giao_dich(self):
        for record in self:
            record.tong_giao_dich = sum(record.giao_dich_ids.mapped("gia_tri"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_khach_hang") or vals.get("ma_khach_hang") == "New":
                vals["ma_khach_hang"] = self.env["ir.sequence"].next_by_code(
                    "qlkh.khach_hang"
                ) or "New"
        return super().create(vals_list)


class QLKHCoHoi(models.Model):
    _name = "qlkh.co_hoi"
    _description = "Cơ hội"
    _order = "ngay_du_kien desc, id desc"

    name = fields.Char("Tên cơ hội", required=True)
    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    gia_tri_du_kien = fields.Float("Giá trị dự kiến")
    giai_doan = fields.Selection(
        [("moi", "Mới"), ("dang_tu_van", "Đang tư vấn"), ("de_xuat", "Đề xuất"), ("thanh_cong", "Thành công"), ("that_bai", "Thất bại")],
        string="Giai đoạn",
        default="moi",
    )
    ngay_du_kien = fields.Date("Ngày dự kiến")
    nguoi_phu_trach = fields.Char("Người phụ trách")
    mo_ta = fields.Text("Mô tả")


class QLKHTuongTac(models.Model):
    _name = "qlkh.tuong_tac"
    _description = "Tương tác"
    _order = "ngay_tuong_tac desc, id desc"

    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    loai_tuong_tac = fields.Selection(
        [("goi_dien", "Gọi điện"), ("email", "Email"), ("hop_mat", "Họp mặt"), ("chat", "Chat")],
        string="Loại tương tác",
        required=True,
    )
    noi_dung = fields.Text("Nội dung")
    ngay_tuong_tac = fields.Datetime("Ngày tương tác", default=fields.Datetime.now)
    ket_qua = fields.Char("Kết quả")


class QLKHHopDong(models.Model):
    _name = "qlkh.hop_dong"
    _description = "Hợp đồng khách hàng"
    _rec_name = "ma_hop_dong"

    ma_hop_dong = fields.Char("Mã hợp đồng", required=True, copy=False, default="New")
    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    gia_tri = fields.Float("Giá trị hợp đồng")
    ngay_bat_dau = fields.Date("Ngày bắt đầu")
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    trang_thai = fields.Selection(
        [("moi", "Mới"), ("hieu_luc", "Hiệu lực"), ("hoan_tat", "Hoàn tất"), ("huy", "Hủy")],
        string="Trạng thái",
        default="moi",
    )
    mo_ta = fields.Text("Mô tả")

    _sql_constraints = [
        ("ma_hop_dong_unique", "unique(ma_hop_dong)", "Mã hợp đồng phải là duy nhất."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ma_hop_dong") or vals.get("ma_hop_dong") == "New":
                vals["ma_hop_dong"] = self.env["ir.sequence"].next_by_code(
                    "qlkh.hop_dong"
                ) or "New"
        return super().create(vals_list)


class QLKHGiaoDich(models.Model):
    _name = "qlkh.giao_dich"
    _description = "Lịch sử giao dịch"
    _order = "ngay_giao_dich desc, id desc"

    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    ten_giao_dich = fields.Char("Tên giao dịch", required=True)
    ngay_giao_dich = fields.Date("Ngày giao dịch", default=fields.Date.today)
    gia_tri = fields.Float("Giá trị")
    trang_thai = fields.Selection(
        [("moi", "Mới"), ("dang_xu_ly", "Đang xử lý"), ("hoan_tat", "Hoàn tất")],
        string="Trạng thái",
        default="moi",
    )
    ghi_chu = fields.Text("Ghi chú")


class QLKHGhiChu(models.Model):
    _name = "qlkh.ghi_chu"
    _description = "Ghi chú khách hàng"
    _order = "ngay_tao desc, id desc"

    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    tieu_de = fields.Char("Tiêu đề", required=True)
    noi_dung = fields.Text("Nội dung")
    ngay_tao = fields.Datetime("Ngày tạo", default=fields.Datetime.now)


class QLKHPhanHoi(models.Model):
    _name = "qlkh.phan_hoi"
    _description = "Phản hồi khách hàng"
    _order = "ngay_phan_hoi desc, id desc"

    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    tieu_de = fields.Char("Tiêu đề", required=True)
    muc_do_hai_long = fields.Selection(
        [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        string="Mức độ hài lòng",
    )
    noi_dung = fields.Text("Nội dung phản hồi")
    ngay_phan_hoi = fields.Date("Ngày phản hồi", default=fields.Date.today)


class QLKHNhiemVu(models.Model):
    _name = "qlkh.nhiem_vu"
    _description = "Nhiệm vụ chăm sóc khách hàng"
    _order = "han_xu_ly asc, id desc"

    ten_nhiem_vu = fields.Char("Tên nhiệm vụ", required=True)
    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng", required=True)
    nguoi_phu_trach = fields.Char("Người phụ trách")
    han_xu_ly = fields.Date("Hạn xử lý")
    muc_do_uu_tien = fields.Selection(
        [("thap", "Thấp"), ("trung_binh", "Trung bình"), ("cao", "Cao")],
        string="Mức độ ưu tiên",
        default="trung_binh",
    )
    trang_thai = fields.Selection(
        [("moi", "Mới"), ("dang_thuc_hien", "Đang thực hiện"), ("hoan_tat", "Hoàn tất")],
        string="Trạng thái",
        default="moi",
    )
    mo_ta = fields.Text("Mô tả")


class QLKHMarketing(models.Model):
    _name = "qlkh.marketing"
    _description = "Chiến dịch marketing khách hàng"
    _order = "ngay_bat_dau desc, id desc"

    ten_chien_dich = fields.Char("Tên chiến dịch", required=True)
    khach_hang_id = fields.Many2one("qlkh.khach_hang", string="Khách hàng")
    kenh = fields.Selection(
        [("email", "Email"), ("sms", "SMS"), ("social", "Social"), ("offline", "Offline")],
        string="Kênh",
        required=True,
    )
    ngan_sach = fields.Float("Ngân sách")
    ngay_bat_dau = fields.Date("Ngày bắt đầu")
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    trang_thai = fields.Selection(
        [("nhap", "Nháp"), ("dang_chay", "Đang chạy"), ("ket_thuc", "Kết thúc")],
        string="Trạng thái",
        default="nhap",
    )
    mo_ta = fields.Text("Mô tả")
