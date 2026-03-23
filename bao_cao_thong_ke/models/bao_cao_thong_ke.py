from odoo import fields, models, tools


class BaoCaoThongKe(models.Model):
    _name = "bao_cao.thong_ke"
    _description = "Báo cáo thống kê tuyển dụng"
    _auto = False
    _order = "month desc, vi_tri_id asc"

    name = fields.Char("Báo cáo", readonly=True)
    month = fields.Date("Tháng", readonly=True)
    vi_tri_id = fields.Many2one(
        "vi_tri_tuyen_dung",
        string="Vị trí ứng tuyển",
        readonly=True,
    )
    candidate_count = fields.Integer("Số ứng viên", readonly=True)
    average_score = fields.Float(
        "Điểm phù hợp trung bình",
        readonly=True,
        digits=(16, 2),
    )
    interview_total = fields.Integer("Tổng số buổi phỏng vấn", readonly=True)
    interview_scheduled = fields.Integer("Buổi đang lên lịch", readonly=True)
    interview_done = fields.Integer("Buổi đã hoàn thành", readonly=True)
    interview_cancelled = fields.Integer("Buổi đã hủy", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, "bao_cao_thong_ke")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW bao_cao_thong_ke AS (
                SELECT
                    row_number() OVER (
                        ORDER BY date_trunc('month', uv.create_date) DESC,
                                 uv.vi_tri_id
                    ) AS id,
                    date_trunc('month', uv.create_date)::date AS month,
                    uv.vi_tri_id AS vi_tri_id,
                    concat(
                        to_char(date_trunc('month', uv.create_date), 'YYYY-MM'),
                        ' - ',
                        coalesce(vt.name, 'Chưa xác định')
                    ) AS name,
                    count(DISTINCT uv.id) AS candidate_count,
                    avg(uv.diem_phu_hop) AS average_score,
                    count(pv.id) AS interview_total,
                    count(pv.id)
                        FILTER (WHERE pv.state = 'scheduled') AS interview_scheduled,
                    count(pv.id)
                        FILTER (WHERE pv.state = 'done') AS interview_done,
                    count(pv.id)
                        FILTER (WHERE pv.state = 'cancelled') AS interview_cancelled
                FROM ung_vien uv
                LEFT JOIN ung_vien_phong_van pv ON pv.ung_vien_id = uv.id
                LEFT JOIN vi_tri_tuyen_dung vt ON vt.id = uv.vi_tri_id
                GROUP BY date_trunc('month', uv.create_date),
                         uv.vi_tri_id,
                         vt.name
            )
            """
        )
