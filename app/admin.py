from flask import session, redirect, url_for
from datetime import datetime
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import flash
from sqlalchemy import func
from app import db
from wtforms import PasswordField
from wtforms.validators import Optional, Length
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
    form_columns = [
        "TenDangNhap", "HoTen", "SoDienThoai",
        "Email", "SoTaiKhoanNganHang",
        "VaiTro", "TrangThaiHoatDong",
    ]
    # [SỬA] Thêm field mật khẩu tùy chỉnh vào form
    # Optional() khi edit (để trống = giữ nguyên), bắt buộc khi create xử lý trong on_model_change
    form_extra_fields = {
        "mat_khau_nhap": PasswordField("Mật khẩu", validators=[Optional(), Length(min=6, max=255)])
    }
    # Đặt thứ tự hiển thị, mat_khau_nhap nằm sau TenDangNhap
    form_columns = [
        "TenDangNhap", "mat_khau_nhap", "HoTen", "SoDienThoai",
        "Email", "SoTaiKhoanNganHang",
        "VaiTro", "TrangThaiHoatDong",
    ]

    def on_model_change(self, form, model, is_created):
        from werkzeug.security import generate_password_hash
        raw_password = form.mat_khau_nhap.data

        if is_created:
            # Tạo mới: bắt buộc phải có mật khẩu
            if not raw_password:
                from wtforms.validators import ValidationError
                raise ValidationError("Mật khẩu không được để trống khi tạo mới.")
            model.MatKhau = generate_password_hash(raw_password)
        else:
            # Chỉnh sửa: chỉ hash nếu admin có nhập mật khẩu mới
            if raw_password:
                model.MatKhau = generate_password_hash(raw_password)
            # Nếu để trống thì giữ nguyên MatKhau cũ — không làm gì

    can_export = True
    page_size  = 20


class KhachSanView(SecureModelView):
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
    # [SỬA] Thay form_excluded_columns bằng form_columns.
    # Dùng "chu_khach_san" (relationship name) thay vì "MaChuKhachSan" (FK int)
    # để Flask-Admin render dropdown chọn chủ khách sạn thay vì ô nhập số thô.
    form_columns = [
        "chu_khach_san",
        "TenKhachSan", "ThanhPho", "DiaChi", "ViTriNoiBat",
        "SoDienThoaiLienHe", "MoTa", "QuyDinhKhachSan",
        "ChinhSachHuy", "ThuMucAnh",
        "TrangThaiDuyet", "LyDoTuChoi", "TrangThaiHoatDong",
    ]
    can_export = True
    page_size  = 20

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
                    hotel.LyDoTuChoi = "Không đáp ứng yêu cầu của hệ thống"
                    count += 1
            db.session.commit()
            flash(f"Đã từ chối {count} khách sạn. Vào tab 'Đã từ chối' để cập nhật lý do.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "error")


class KhachSanTuChoiView(SecureModelView):
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
    can_delete = False
    can_export = True
    page_size  = 20
    # [SỬA] Xóa can_edit = False bị khai báo trùng rồi ghi đè bởi can_edit = True bên dưới.
    # Giữ lại 1 lần duy nhất can_edit = True cho rõ ràng.
    can_edit = True
    form_columns = ["LyDoTuChoi"]


# =========================================================
# [MỚI] LoaiPhongView — tách riêng thay vì dùng SecureModelView trơn
# Nguyên nhân lỗi gốc: SecureModelView không có form_columns nên
# MaKhachSan (NOT NULL) bị bỏ qua → IntegrityError khi Create.
# Dùng relationship name "khach_san" để Flask-Admin render dropdown.
# =========================================================
class LoaiPhongView(SecureModelView):
    column_list = ["MaLoaiPhong", "khach_san", "TenLoaiPhong",
                   "GiaMoiDem", "SoNguoiToiDa", "SoLuongPhong", "TrangThaiHoatDong"]
    column_searchable_list = ["TenLoaiPhong"]
    column_filters         = ["TrangThaiHoatDong", "khach_san"]
    column_labels = {
        "khach_san": "Khách sạn", "TenLoaiPhong": "Tên loại phòng",
        "GiaMoiDem": "Giá/đêm", "SoNguoiToiDa": "Số người tối đa",
        "SoLuongPhong": "Số lượng phòng", "TrangThaiHoatDong": "Trạng thái"
    }
    # [SỬA] Khai báo form_columns rõ ràng, dùng "khach_san" (relationship)
    # để hiện dropdown thay vì để MaKhachSan bị null.
    form_columns = [
        "khach_san",
        "TenLoaiPhong", "MoTa",
        "GiaMoiDem", "SoNguoiToiDa", "SoLuongPhong",
        "ThuMucAnh", "TrangThaiHoatDong",
    ]
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
    # [SỬA] Thay form_excluded_columns bằng form_columns.
    # Dùng relationship names "nguoi_dung" và "khach_san" để hiện dropdown,
    # tránh MaNguoiDung / MaKhachSan bị null khi admin tạo đặt phòng mới.
    form_columns = [
        "MaDatPhongCode",
        "nguoi_dung",
        "khach_san",
        "NgayNhanPhong", "NgayTraPhong",
        "SoNguoiLuuTru", "TongTien",
        "TrangThaiDatPhong",
    ]
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
    # [SỬA] Thêm form_columns: dùng "dat_phong" (relationship) để hiện dropdown
    # đơn đặt phòng thay vì để MaDatPhong bị null khi tạo thanh toán mới.
    form_columns = [
        "dat_phong",
        "PhuongThucThanhToan", "TrangThaiThanhToan",
        "SoTienThanhToan", "MaGiaoDich", "ThoiGianThanhToan",
    ]
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
    # [SỬA] Thêm form_columns: dùng relationship names để hiện dropdown,
    # tránh MaNguoiDung / MaKhachSan / MaDatPhong bị null khi tạo đánh giá.
    form_columns = [
        "dat_phong",
        "nguoi_dung",
        "khach_san",
        "SoSao", "BinhLuan",
    ]
    can_export = True
    page_size  = 20


# =========================================================
# [MỚI] HoanTienView — tách riêng thay vì dùng SecureModelView trơn
# để tránh MaDatPhong bị null khi tạo hoàn tiền mới.
# =========================================================
class HoanTienView(SecureModelView):
    column_list = ["MaHoanTien", "dat_phong", "SoTienHoan",
                   "LyDoHoanTien", "TrangThaiHoanTien", "ThoiGianHoanTien"]
    column_labels = {
        "dat_phong": "Đơn đặt", "SoTienHoan": "Số tiền hoàn",
        "LyDoHoanTien": "Lý do", "TrangThaiHoanTien": "Trạng thái",
        "ThoiGianHoanTien": "Thời gian"
    }
    # [SỬA] Khai báo form_columns với "dat_phong" relationship
    # để hiện dropdown thay vì ô nhập MaDatPhong thô.
    form_columns = [
        "dat_phong",
        "SoTienHoan", "LyDoHoanTien",
        "TrangThaiHoanTien", "ThoiGianHoanTien",
    ]
    can_export = True
    page_size  = 20


# =========================================================
# [MỚI] ChuyenTienView — tách riêng thay vì dùng SecureModelView trơn
# để tránh MaDatPhong / MaKhachSan bị null khi tạo bản ghi mới.
# =========================================================
class ChuyenTienView(SecureModelView):
    column_list = ["MaChuyenTien", "dat_phong", "khach_san",
                   "TongTienDonHang", "PhiHeThong",
                   "SoTienChuyenChoKhachSan", "TrangThaiChuyenTien", "ThoiGianChuyenTien"]
    column_labels = {
        "dat_phong": "Đơn đặt", "khach_san": "Khách sạn",
        "TongTienDonHang": "Tổng đơn", "PhiHeThong": "Phí hệ thống",
        "SoTienChuyenChoKhachSan": "Tiền chuyển KS",
        "TrangThaiChuyenTien": "Trạng thái", "ThoiGianChuyenTien": "Thời gian"
    }
    # [SỬA] Khai báo form_columns với relationship names
    # để hiện dropdown thay vì ô nhập FK thô.
    form_columns = [
        "dat_phong",
        "khach_san",
        "TongTienDonHang", "PhiHeThong",
        "SoTienChuyenChoKhachSan",
        "TrangThaiChuyenTien", "ThoiGianChuyenTien",
    ]
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
    # [SỬA] Thay SecureModelView trơn bằng LoaiPhongView có form_columns đầy đủ
    admin.add_view(LoaiPhongView(LoaiPhong,   db.session, name="Loại phòng",  category="Quản lý"))
    admin.add_view(DatPhongView(DatPhong,     db.session, name="Đặt phòng",   category="Quản lý"))
    admin.add_view(ThanhToanView(ThanhToan,   db.session, name="Thanh toán",  category="Quản lý"))
    # [SỬA] Thay SecureModelView trơn bằng HoanTienView
    admin.add_view(HoanTienView(HoanTien,     db.session, name="Hoàn tiền",   category="Quản lý"))
    admin.add_view(DanhGiaView(DanhGia,       db.session, name="Đánh giá",    category="Quản lý"))
    # [SỬA] Thay SecureModelView trơn bằng ChuyenTienView
    admin.add_view(ChuyenTienView(ChuyenTienKhachSan, db.session, name="Chuyển tiền", category="Quản lý"))
    admin.add_view(SecureModelView(TienIch,   db.session, name="Tiện ích",    category="Cấu hình"))

    return admin