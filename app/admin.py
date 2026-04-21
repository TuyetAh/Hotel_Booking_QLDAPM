from flask import session, redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
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
    column_list            = ["MaKhachSan", "TenKhachSan", "ThanhPho", "DiaChi", "TrangThaiDuyet", "TrangThaiHoatDong", "DiemDanhGiaTrungBinh", "NgayTao"]
    column_searchable_list = ["TenKhachSan", "ThanhPho", "DiaChi"]
    column_filters         = ["TrangThaiDuyet", "TrangThaiHoatDong", "ThanhPho"]
    column_labels          = {
        "MaKhachSan": "Mã", "TenKhachSan": "Tên KS", "ThanhPho": "Thành phố",
        "TrangThaiDuyet": "Duyệt", "TrangThaiHoatDong": "Hoạt động",
        "DiemDanhGiaTrungBinh": "Điểm TB", "NgayTao": "Ngày tạo"
    }
    form_excluded_columns  = ["loai_phongs", "dat_phongs", "danh_gias", "chuyen_tien_khach_sans", "tien_ichs"]
    can_export = True
    page_size  = 20


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
    admin.add_view(KhachSanView(KhachSan,     db.session, name="Khách sạn",   category="Quản lý"))
    admin.add_view(SecureModelView(LoaiPhong, db.session, name="Loại phòng",  category="Quản lý"))
    admin.add_view(DatPhongView(DatPhong,     db.session, name="Đặt phòng",   category="Quản lý"))
    admin.add_view(ThanhToanView(ThanhToan,   db.session, name="Thanh toán",  category="Quản lý"))
    admin.add_view(SecureModelView(HoanTien,  db.session, name="Hoàn tiền",   category="Quản lý"))
    admin.add_view(DanhGiaView(DanhGia,       db.session, name="Đánh giá",    category="Quản lý"))
    admin.add_view(SecureModelView(ChuyenTienKhachSan, db.session, name="Chuyển tiền", category="Quản lý"))
    admin.add_view(SecureModelView(TienIch,   db.session, name="Tiện ích",    category="Cấu hình"))

    return admin