from flask import session, redirect, url_for
from datetime import datetime
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import flash
from sqlalchemy import func
from app import db
from app.models import (
    NguoiDung, ChuKhachSan, KhachSan,
    TienIch, LoaiPhong, DatPhong,
    ChiTietDatPhong, ThanhToan, HoanTien,
    DanhGia, ChuyenTienKhachSan
)


# =========================================================
# BẢO MẬT
# =========================================================
class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get("vai_tro") == 0

    def inaccessible_callback(self, name, **kwargs):
        return redirect("/dang-nhap")


# =========================================================
# DASHBOARD
# =========================================================
class DashboardView(AdminIndexView):
    @expose("/")
    def index(self):
        if session.get("vai_tro") != 0:
            return redirect("/dang-nhap")

        stats = {
            "total_users":    NguoiDung.query.count(),
            "total_hotels":   KhachSan.query.count(),
            "total_bookings": DatPhong.query.count(),
            "pending_bookings":   DatPhong.query.filter_by(TrangThaiDatPhong=0).count(),
            "confirmed_bookings": DatPhong.query.filter_by(TrangThaiDatPhong=1).count(),
            "cancelled_bookings": DatPhong.query.filter_by(TrangThaiDatPhong=2).count(),
            "completed_bookings": DatPhong.query.filter_by(TrangThaiDatPhong=3).count(),
            "total_revenue": db.session.query(
                func.sum(ThanhToan.SoTienThanhToan)
            ).filter_by(TrangThaiThanhToan=1).scalar() or 0,
            "recent_bookings": DatPhong.query.order_by(
                DatPhong.NgayTao.desc()
            ).limit(10).all(),
        }
        return self.render("admin/index.html", stats=stats)


# =========================================================
# VIEWS
# =========================================================
class NguoiDungView(SecureModelView):
    column_list            = ["MaNguoiDung", "TenDangNhap", "HoTen", "Email", "SoDienThoai", "VaiTro", "TrangThaiHoatDong", "NgayTao"]
    column_searchable_list = ["TenDangNhap", "HoTen", "Email"]
    column_filters         = ["VaiTro", "TrangThaiHoatDong"]
    column_labels          = {
        "MaNguoiDung": "Mã", "TenDangNhap": "Tên đăng nhập",
        "HoTen": "Họ tên", "Email": "Email", "SoDienThoai": "SĐT",
        "VaiTro": "Vai trò", "TrangThaiHoatDong": "Trạng thái", "NgayTao": "Ngày tạo"
    }
    form_excluded_columns  = ["MatKhau", "dat_phongs", "danh_gias", "chu_khach_san"]
    can_export = True
    page_size  = 20



class KhachSanView(SecureModelView):
    # Chỉ hiện KS đã duyệt (TrangThaiDuyet = 1)
    def get_query(self):
        return self.session.query(self.model).filter(
            self.model.TrangThaiDuyet == 1
        )

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(
            self.model.TrangThaiDuyet == 1
        )

    column_list = ["MaKhachSan", "TenKhachSan", "ThanhPho", "DiaChi",
                   "TrangThaiDuyet", "TrangThaiHoatDong",
                   "DiemDanhGiaTrungBinh", "NgayTao"]
    column_searchable_list = ["TenKhachSan", "ThanhPho", "DiaChi"]
    column_filters         = ["TrangThaiHoatDong", "ThanhPho"]
    column_labels          = {
        "MaKhachSan": "Mã", "TenKhachSan": "Tên KS", "ThanhPho": "Thành phố",
        "TrangThaiDuyet": "Duyệt", "TrangThaiHoatDong": "Hoạt động",
        "DiemDanhGiaTrungBinh": "Điểm TB", "NgayTao": "Ngày tạo"
    }
    form_excluded_columns = ["loai_phongs", "dat_phongs", "danh_gias",
                              "chuyen_tien_khach_sans", "tien_ichs"]
    can_export = True
    page_size  = 20

    # ← THÊM 2 ACTION NÀY
    @action("duyet", "✅ Duyệt", "Bạn có chắc muốn duyệt các khách sạn đã chọn?")
    def action_duyet(self, ids):
        try:
            count = 0
            for id in ids:
                hotel = KhachSan.query.get(id)
                if hotel:
                    hotel.TrangThaiDuyet = 1
                    hotel.NgayDuyet = datetime.now()
                    hotel.LyDoTuChoi = None
                    count += 1
            db.session.commit()
            flash(f"Đã duyệt {count} khách sạn.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "error")

    @action("tu_choi", "❌ Từ chối", "Bạn có chắc muốn từ chối các khách sạn đã chọn?")
    def action_tu_choi(self, ids):
        try:
            count = 0
            for id in ids:
                hotel = KhachSan.query.get(id)
                if hotel:
                    hotel.TrangThaiDuyet = 2
                    hotel.NgayDuyet = None
                    count += 1
            db.session.commit()
            flash(f"Đã từ chối {count} khách sạn.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "error")

class KhachSanChoDuyetView(SecureModelView):
    # Chỉ hiện KS chờ duyệt (TrangThaiDuyet = 0)
    def get_query(self):
        return self.session.query(self.model).filter(
            self.model.TrangThaiDuyet == 0
        )

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(
            self.model.TrangThaiDuyet == 0
        )

    column_list = ["MaKhachSan", "TenKhachSan", "ThanhPho",
                   "DiaChi", "SoDienThoaiLienHe", "NgayTao"]
    column_labels = {
        "MaKhachSan": "Mã", "TenKhachSan": "Tên KS",
        "ThanhPho": "Thành phố", "DiaChi": "Địa chỉ",
        "SoDienThoaiLienHe": "SĐT", "NgayTao": "Ngày gửi"
    }
    can_create = False
    can_delete = False
    can_edit   = False
    can_export = True
    page_size  = 20

    @action("duyet", "✅ Duyệt", "Duyệt các khách sạn đã chọn?")
    def action_duyet(self, ids):
        try:
            count = 0
            for id in ids:
                hotel = KhachSan.query.get(id)
                if hotel:
                    hotel.TrangThaiDuyet = 1
                    hotel.NgayDuyet = datetime.now()
                    hotel.LyDoTuChoi = None
                    count += 1
            db.session.commit()
            flash(f"Đã duyệt {count} khách sạn.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "error")

    @action("tu_choi", "❌ Từ chối", "Từ chối các khách sạn đã chọn?")
    def action_tu_choi(self, ids):
        try:
            count = 0
            for id in ids:
                hotel = KhachSan.query.get(id)
                if hotel:
                    hotel.TrangThaiDuyet = 2
                    hotel.NgayDuyet = None
                    # Lý do mặc định, admin có thể sửa sau trong edit
                    hotel.LyDoTuChoi = "Không đáp ứng yêu cầu của hệ thống"
                    count += 1
            db.session.commit()
            flash(f"Đã từ chối {count} khách sạn. Vào tab 'Đã từ chối' để cập nhật lý do.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "error")

class KhachSanTuChoiView(SecureModelView):
    # Chỉ hiện KS đã từ chối (TrangThaiDuyet = 2)
    def get_query(self):
        return self.session.query(self.model).filter(
            self.model.TrangThaiDuyet == 2
        )

    def get_count_query(self):
        return self.session.query(func.count('*')).filter(
            self.model.TrangThaiDuyet == 2
        )

    column_list = ["MaKhachSan", "TenKhachSan", "ThanhPho",
                   "DiaChi", "LyDoTuChoi", "NgayTao"]
    column_labels = {
        "MaKhachSan": "Mã", "TenKhachSan": "Tên KS",
        "ThanhPho": "Thành phố", "DiaChi": "Địa chỉ",
        "LyDoTuChoi": "Lý do từ chối", "NgayTao": "Ngày gửi"
    }
    can_create = False
    can_edit   = False
    can_delete = False
    can_export = True
    page_size  = 20
    can_edit = True
    form_columns = ["LyDoTuChoi"]

class DatPhongView(SecureModelView):
    column_list            = ["MaDatPhong", "MaDatPhongCode", "nguoi_dung", "khach_san", "NgayNhanPhong", "NgayTraPhong", "TongTien", "TrangThaiDatPhong", "NgayTao"]
    column_searchable_list = ["MaDatPhongCode"]
    column_filters         = ["TrangThaiDatPhong"]
    column_labels          = {
        "MaDatPhongCode": "Mã code", "nguoi_dung": "Khách hàng",
        "khach_san": "Khách sạn", "NgayNhanPhong": "Nhận phòng",
        "NgayTraPhong": "Trả phòng", "TongTien": "Tổng tiền",
        "TrangThaiDatPhong": "Trạng thái", "NgayTao": "Ngày đặt"
    }
    form_excluded_columns  = ["chi_tiet_dat_phongs", "thanh_toan", "hoan_tien", "danh_gia", "chuyen_tien_khach_san"]
    can_delete = False
    can_export = True
    page_size  = 20


class ThanhToanView(SecureModelView):
    column_list    = ["MaThanhToan", "dat_phong", "PhuongThucThanhToan", "TrangThaiThanhToan", "SoTienThanhToan", "ThoiGianThanhToan"]
    column_filters = ["TrangThaiThanhToan", "PhuongThucThanhToan"]
    column_labels  = {
        "dat_phong": "Đơn đặt", "PhuongThucThanhToan": "Phương thức",
        "TrangThaiThanhToan": "Trạng thái", "SoTienThanhToan": "Số tiền",
        "ThoiGianThanhToan": "Thời gian"
    }
    can_delete = False
    can_export = True
    page_size  = 20


class DanhGiaView(SecureModelView):
    column_list            = ["MaDanhGia", "nguoi_dung", "khach_san", "SoSao", "BinhLuan", "NgayDanhGia"]
    column_searchable_list = ["BinhLuan"]
    column_filters         = ["SoSao"]
    column_labels          = {
        "nguoi_dung": "Khách hàng", "khach_san": "Khách sạn",
        "SoSao": "Số sao", "BinhLuan": "Bình luận", "NgayDanhGia": "Ngày đánh giá"
    }
    can_export = True
    page_size  = 20


# =========================================================
# KHỞI TẠO ADMIN
# =========================================================
def init_admin(app):
    admin = Admin(
        app,
        name="Hotel Booking Admin",
        template_mode="bootstrap3",
        index_view=DashboardView(name="Dashboard", url="/admin")
    )

    admin.add_view(NguoiDungView(NguoiDung,   db.session, name="Người dùng",  category="Quản lý"))
    admin.add_view(KhachSanChoDuyetView(KhachSan, db.session,
                                        name="⏳ Chờ duyệt",
                                        endpoint="khachsan_cho_duyet",
                                        category="Duyệt KS"))
    admin.add_view(KhachSanTuChoiView(KhachSan, db.session,
                                      name="❌ Đã từ chối",
                                      endpoint="khachsan_tu_choi",
                                      category="Duyệt KS"))
    admin.add_view(KhachSanView(KhachSan, db.session,
                                name="🏨 Tất cả KS",
                                endpoint="khachsan_tat_ca",
                                category="Duyệt KS"))
    admin.add_view(KhachSanView(KhachSan,     db.session, name="Khách sạn",   category="Quản lý"))
    admin.add_view(SecureModelView(LoaiPhong, db.session, name="Loại phòng",  category="Quản lý"))
    admin.add_view(DatPhongView(DatPhong,     db.session, name="Đặt phòng",   category="Quản lý"))
    admin.add_view(ThanhToanView(ThanhToan,   db.session, name="Thanh toán",  category="Quản lý"))
    admin.add_view(SecureModelView(HoanTien,  db.session, name="Hoàn tiền",   category="Quản lý"))
    admin.add_view(DanhGiaView(DanhGia,       db.session, name="Đánh giá",    category="Quản lý"))
    admin.add_view(SecureModelView(ChuyenTienKhachSan, db.session, name="Chuyển tiền", category="Quản lý"))
    admin.add_view(SecureModelView(TienIch,   db.session, name="Tiện ích",    category="Cấu hình"))

    return admin