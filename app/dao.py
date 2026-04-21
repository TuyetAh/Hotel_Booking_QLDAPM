import os
import shutil
from datetime import datetime
from decimal import Decimal

from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import current_app


from app import db
from app.models import (
    NguoiDung,
    ChuKhachSan,
    KhachSan,
    TienIch,
    TienIchKhachSan,
    LoaiPhong,
    TienIchLoaiPhong,
    DatPhong,
    ChiTietDatPhong,
    ThanhToan,
    HoanTien,
    DanhGia,
    ChuyenTienKhachSan
)

# =========================================================
# 1. HẰNG SỐ / MAPPING HIỂN THỊ
# =========================================================

VAI_TRO_TEXT = {
    0: "Quản trị viên",
    1: "Chủ khách sạn",
    2: "Khách hàng"
}

TRANG_THAI_HOAT_DONG_TEXT = {
    0: "Dừng hoạt động",
    1: "Đang hoạt động"
}

CHINH_SACH_HUY_TEXT = {
    0: "Trước 1 ngày",
    1: "Trước 3 ngày",
    2: "Không cho hủy"
}

TRANG_THAI_DUYET_TEXT = {
    0: "Chờ duyệt",
    1: "Đã duyệt",
    2: "Từ chối"
}

TRANG_THAI_DAT_PHONG_TEXT = {
    0: "Chờ thanh toán",
    1: "Đã thanh toán",
    2: "Đã hủy",
    3: "Hoàn thành"
}

TRANG_THAI_THANH_TOAN_TEXT = {
    0: "Chờ thanh toán",
    1: "Thành công",
    2: "Thất bại",
    3: "Đã hoàn tiền"
}

TRANG_THAI_HOAN_TIEN_TEXT = {
    0: "Chờ xử lý",
    1: "Thành công",
    2: "Thất bại"
}

TRANG_THAI_CHUYEN_TIEN_TEXT = {
    0: "Chờ chuyển tiền",
    1: "Đã chuyển",
    2: "Thất bại"
}


# =========================================================
# 2. HÀM HỖ TRỢ HIỂN THỊ TEXT
# =========================================================

def hien_thi_vai_tro(value):
    return VAI_TRO_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_hoat_dong(value):
    return TRANG_THAI_HOAT_DONG_TEXT.get(value, "Không xác định")


def hien_thi_chinh_sach_huy(value):
    return CHINH_SACH_HUY_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_duyet(value):
    return TRANG_THAI_DUYET_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_dat_phong(value):
    return TRANG_THAI_DAT_PHONG_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_thanh_toan(value):
    return TRANG_THAI_THANH_TOAN_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_hoan_tien(value):
    return TRANG_THAI_HOAN_TIEN_TEXT.get(value, "Không xác định")


def hien_thi_trang_thai_chuyen_tien(value):
    return TRANG_THAI_CHUYEN_TIEN_TEXT.get(value, "Không xác định")


# =========================================================
# 3. HÀM HỖ TRỢ XỬ LÝ ẢNH TỪ THƯ MỤC
#
# ThuMucAnh trong DB ví dụ:
# - khachsan/ks_1
# - loaiphong/lp_1
#
# Đường dẫn thật:
# app/static/images/khachsan/ks_1
# =========================================================

def lay_duong_dan_thu_muc_anh(relative_folder):
    """
    Chuyển ThuMucAnh trong DB thành đường dẫn tuyệt đối trong project.

    Ví dụ:
    relative_folder = 'khachsan/ks_1'

    Kết quả:
    .../app/static/images/khachsan/ks_1
    """
    if not relative_folder:
        return None

    return os.path.join(current_app.root_path, "static", "images", relative_folder)


def lay_danh_sach_anh_va_loi(relative_folder):
    """
    Trả về:
        (danh_sach_anh, thong_bao_loi)

    danh_sach_anh: list dùng cho url_for('static', filename=...)
    ví dụ:
        ['images/khachsan/ks_1/1.jpg', 'images/khachsan/ks_1/2.jpg']

    thong_bao_loi:
        None nếu không lỗi
        chuỗi mô tả nếu có vấn đề
    """
    if not relative_folder:
        return [], "Khách sạn chưa có ThuMucAnh trong database"

    folder_path = lay_duong_dan_thu_muc_anh(relative_folder)

    if not folder_path:
        return [], "Không tạo được đường dẫn thư mục ảnh"

    if not os.path.exists(folder_path):
        return [], f"Không tìm thấy thư mục ảnh: {folder_path}"

    if not os.path.isdir(folder_path):
        return [], f"Đường dẫn không phải thư mục: {folder_path}"

    valid_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    image_files = []

    for file_name in os.listdir(folder_path):
        full_file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(full_file_path) and file_name.lower().endswith(valid_extensions):
            image_files.append(file_name)

    image_files.sort()

    if not image_files:
        return [], f"Thư mục có tồn tại nhưng không có file ảnh hợp lệ: {folder_path}"

    result = [f"images/{relative_folder}/{file_name}" for file_name in image_files]
    return result, None

def lay_danh_sach_anh(relative_folder):
    ds_anh, _ = lay_danh_sach_anh_va_loi(relative_folder)
    return ds_anh


def lay_anh_dau_tien_va_loi(relative_folder):
    """
    Trả về:
        (anh_dau_tien, thong_bao_loi)
    """
    ds_anh, loi = lay_danh_sach_anh_va_loi(relative_folder)

    if ds_anh:
        return ds_anh[0], None

    return None, loi


def lay_anh_dau_tien(relative_folder):
    anh, _ = lay_anh_dau_tien_va_loi(relative_folder)
    return anh






def xoa_thu_muc_anh(relative_folder):
    """
    Xóa cả thư mục ảnh khi admin từ chối hoặc khi cần dọn dữ liệu.
    """
    if not relative_folder:
        return False

    folder_path = lay_duong_dan_thu_muc_anh(relative_folder)

    if folder_path and os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        return True

    return False


# =========================================================
# 4. NGƯỜI DÙNG / ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================

def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)


def get_user_by_username(username):
    return NguoiDung.query.filter_by(TenDangNhap=username).first()


def get_user_by_email(email):
    return NguoiDung.query.filter_by(Email=email).first()


def check_login(username, password):
    user = NguoiDung.query.filter_by(TenDangNhap=username).first()

    if not user:
        return None

    # Tài khoản bị khóa
    if user.TrangThaiHoatDong != 1:
        return None

    # Thử hash trước
    try:
        if check_password_hash(user.MatKhau, password):
            return user
    except Exception:
        pass

    # Dữ liệu mẫu đang là text thường (123456)
    if user.MatKhau == password:
        return user

    return None


def register_user(ten_dang_nhap, mat_khau, ho_ten, so_dien_thoai, email,
                  so_tai_khoan_ngan_hang=None, vai_tro=2):
    """
    Đăng ký user mới.
    Mặc định là khách hàng.
    """
    if get_user_by_username(ten_dang_nhap):
        return False, "Tên đăng nhập đã tồn tại"

    if get_user_by_email(email):
        return False, "Email đã được sử dụng"

    hashed_password = generate_password_hash(mat_khau)

    new_user = NguoiDung(
        TenDangNhap=ten_dang_nhap,
        MatKhau=hashed_password,
        HoTen=ho_ten,
        SoDienThoai=so_dien_thoai,
        Email=email,
        SoTaiKhoanNganHang=so_tai_khoan_ngan_hang,
        VaiTro=vai_tro,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return True, new_user
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi đăng ký: {str(e)}"


def create_hotel_owner_account(ten_dang_nhap, mat_khau, ho_ten, so_dien_thoai,
                               email, so_tai_khoan_ngan_hang=None,
                               ten_doanh_nghiep=None, dia_chi_doanh_nghiep=None):
    """
    Tạo tài khoản chủ khách sạn.
    """
    if get_user_by_username(ten_dang_nhap):
        return False, "Tên đăng nhập đã tồn tại"

    if get_user_by_email(email):
        return False, "Email đã được sử dụng"

    hashed_password = generate_password_hash(mat_khau)

    try:
        owner_user = NguoiDung(
            TenDangNhap=ten_dang_nhap,
            MatKhau=hashed_password,
            HoTen=ho_ten,
            SoDienThoai=so_dien_thoai,
            Email=email,
            SoTaiKhoanNganHang=so_tai_khoan_ngan_hang,
            VaiTro=1,
            TrangThaiHoatDong=1
        )
        db.session.add(owner_user)
        db.session.flush()

        owner_info = ChuKhachSan(
            MaNguoiDung=owner_user.MaNguoiDung,
            TenDoanhNghiep=ten_doanh_nghiep,
            DiaChiDoanhNghiep=dia_chi_doanh_nghiep
        )
        db.session.add(owner_info)

        db.session.commit()
        return True, owner_user
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo tài khoản chủ khách sạn: {str(e)}"


def is_admin(user):
    return user is not None and user.VaiTro == 0


def is_hotel_owner(user):
    return user is not None and user.VaiTro == 1


def is_customer(user):
    return user is not None and user.VaiTro == 2


# =========================================================
# 5. KHÁCH SẠN
# =========================================================

def get_all_hotels():
    """
    Lấy tất cả khách sạn đã duyệt và đang hoạt động.
    """
    return KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    ).order_by(KhachSan.NgayTao.desc()).all()


def get_featured_hotels(limit=6):
    """
    Lấy khách sạn nổi bật.
    """
    return KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    ).order_by(
        KhachSan.DiemDanhGiaTrungBinh.desc(),
        KhachSan.NgayTao.desc()
    ).limit(limit).all()


def get_hotel_by_id(hotel_id):
    return KhachSan.query.get(hotel_id)


def get_hotels_by_city(city_name):
    return KhachSan.query.filter(
        KhachSan.ThanhPho.ilike(f"%{city_name}%"),
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    ).all()


def search_hotels(keyword=None, city=None):
    """
    Tìm kiếm khách sạn theo từ khóa / thành phố.
    """
    query = KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1
    )

    if keyword:
        query = query.filter(
            or_(
                KhachSan.TenKhachSan.ilike(f"%{keyword}%"),
                KhachSan.DiaChi.ilike(f"%{keyword}%"),
                KhachSan.ViTriNoiBat.ilike(f"%{keyword}%")
            )
        )

    if city:
        query = query.filter(KhachSan.ThanhPho.ilike(f"%{city}%"))

    return query.order_by(KhachSan.NgayTao.desc()).all()


def create_hotel(ma_chu_khach_san, ten_khach_san, thanh_pho, dia_chi,
                 vi_tri_noi_bat, so_dien_thoai_lien_he, mo_ta,
                 quy_dinh_khach_san, chinh_sach_huy, thu_muc_anh=None):
    """
    Tạo khách sạn mới ở trạng thái chờ duyệt.
    """
    new_hotel = KhachSan(
        MaChuKhachSan=ma_chu_khach_san,
        TenKhachSan=ten_khach_san,
        ThanhPho=thanh_pho,
        DiaChi=dia_chi,
        ViTriNoiBat=vi_tri_noi_bat,
        SoDienThoaiLienHe=so_dien_thoai_lien_he,
        MoTa=mo_ta,
        QuyDinhKhachSan=quy_dinh_khach_san,
        ChinhSachHuy=chinh_sach_huy,
        ThuMucAnh=thu_muc_anh,
        TrangThaiDuyet=0,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(new_hotel)
        db.session.commit()
        return True, new_hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo khách sạn: {str(e)}"


def update_hotel(hotel_id, **kwargs):
    """
    Cập nhật thông tin khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    allowed_fields = [
        "TenKhachSan", "ThanhPho", "DiaChi", "ViTriNoiBat",
        "SoDienThoaiLienHe", "MoTa", "QuyDinhKhachSan",
        "ChinhSachHuy", "ThuMucAnh", "TrangThaiHoatDong"
    ]

    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(hotel, field, value)

    hotel.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật khách sạn: {str(e)}"


def get_hotel_images(hotel):
    """
    Lấy danh sách ảnh của khách sạn từ ThuMucAnh.
    """
    if not hotel:
        return []
    return lay_danh_sach_anh(hotel.ThuMucAnh)


def get_hotel_cover_image(hotel):
    """
    Lấy ảnh đầu tiên của khách sạn.
    """
    if not hotel:
        return None
    return lay_anh_dau_tien(hotel.ThuMucAnh)


def get_hotel_detail_data(hotel_id):
    """
    Gom dữ liệu chi tiết khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return None

    data = {
        "hotel": hotel,
        "hotel_images": get_hotel_images(hotel),
        "hotel_cover": get_hotel_cover_image(hotel),
        "room_types": get_room_types_by_hotel(hotel_id),
        "reviews": get_reviews_by_hotel(hotel_id),
        "tien_ichs": hotel.tien_ichs,
        "chinh_sach_huy_text": hien_thi_chinh_sach_huy(hotel.ChinhSachHuy),
        "trang_thai_duyet_text": hien_thi_trang_thai_duyet(hotel.TrangThaiDuyet),
        "trang_thai_hoat_dong_text": hien_thi_trang_thai_hoat_dong(hotel.TrangThaiHoatDong)
    }
    return data


# =========================================================
# 6. LOẠI PHÒNG
# =========================================================

def get_room_type_by_id(room_type_id):
    return LoaiPhong.query.get(room_type_id)


def get_room_types_by_hotel(hotel_id):
    return LoaiPhong.query.filter_by(
        MaKhachSan=hotel_id,
        TrangThaiHoatDong=1
    ).all()


def create_room_type(ma_khach_san, ten_loai_phong, mo_ta,
                     gia_moi_dem, so_nguoi_toi_da, so_luong_phong,
                     thu_muc_anh=None):
    """
    Tạo loại phòng.
    """
    room_type = LoaiPhong(
        MaKhachSan=ma_khach_san,
        TenLoaiPhong=ten_loai_phong,
        MoTa=mo_ta,
        GiaMoiDem=gia_moi_dem,
        SoNguoiToiDa=so_nguoi_toi_da,
        SoLuongPhong=so_luong_phong,
        ThuMucAnh=thu_muc_anh,
        TrangThaiHoatDong=1
    )

    try:
        db.session.add(room_type)
        db.session.commit()
        return True, room_type
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo loại phòng: {str(e)}"


def update_room_type(room_type_id, **kwargs):
    room_type = get_room_type_by_id(room_type_id)
    if not room_type:
        return False, "Không tìm thấy loại phòng"

    allowed_fields = [
        "TenLoaiPhong", "MoTa", "GiaMoiDem",
        "SoNguoiToiDa", "SoLuongPhong",
        "ThuMucAnh", "TrangThaiHoatDong"
    ]

    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(room_type, field, value)

    room_type.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, room_type
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật loại phòng: {str(e)}"


def get_room_images(room_type):
    if not room_type:
        return []
    return lay_danh_sach_anh(room_type.ThuMucAnh)


def get_room_cover_image(room_type):
    if not room_type:
        return None
    return lay_anh_dau_tien(room_type.ThuMucAnh)


# =========================================================
# 7. TIỆN ÍCH
# =========================================================

def get_all_tien_ich():
    return TienIch.query.order_by(TienIch.TenTienIch.asc()).all()


def add_tien_ich_to_hotel(ma_khach_san, ma_tien_ich):
    existing = TienIchKhachSan.query.filter_by(
        MaKhachSan=ma_khach_san,
        MaTienIch=ma_tien_ich
    ).first()

    if existing:
        return False, "Tiện ích đã tồn tại trong khách sạn"

    item = TienIchKhachSan(
        MaKhachSan=ma_khach_san,
        MaTienIch=ma_tien_ich
    )

    try:
        db.session.add(item)
        db.session.commit()
        return True, item
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi thêm tiện ích khách sạn: {str(e)}"


def add_tien_ich_to_room_type(ma_loai_phong, ma_tien_ich):
    existing = TienIchLoaiPhong.query.filter_by(
        MaLoaiPhong=ma_loai_phong,
        MaTienIch=ma_tien_ich
    ).first()

    if existing:
        return False, "Tiện ích đã tồn tại trong loại phòng"

    item = TienIchLoaiPhong(
        MaLoaiPhong=ma_loai_phong,
        MaTienIch=ma_tien_ich
    )

    try:
        db.session.add(item)
        db.session.commit()
        return True, item
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi thêm tiện ích loại phòng: {str(e)}"


# =========================================================
# 8. REVIEW / ĐÁNH GIÁ
# =========================================================

def get_reviews_by_hotel(hotel_id):
    return DanhGia.query.filter_by(MaKhachSan=hotel_id).order_by(
        DanhGia.NgayDanhGia.desc()
    ).all()


def get_review_count_by_hotel(hotel_id):
    return DanhGia.query.filter_by(MaKhachSan=hotel_id).count()


def update_hotel_average_rating(hotel_id):
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False

    reviews = DanhGia.query.filter_by(MaKhachSan=hotel_id).all()

    if len(reviews) == 0:
        hotel.DiemDanhGiaTrungBinh = 0
    else:
        total_star = sum(review.SoSao for review in reviews)
        avg_star = round(total_star / len(reviews), 2)
        hotel.DiemDanhGiaTrungBinh = avg_star

    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def add_review(ma_dat_phong, ma_nguoi_dung, ma_khach_san, so_sao, binh_luan=None):
    existing_review = DanhGia.query.filter_by(MaDatPhong=ma_dat_phong).first()
    if existing_review:
        return False, "Đơn đặt phòng này đã được đánh giá"

    review = DanhGia(
        MaDatPhong=ma_dat_phong,
        MaNguoiDung=ma_nguoi_dung,
        MaKhachSan=ma_khach_san,
        SoSao=so_sao,
        BinhLuan=binh_luan
    )

    try:
        db.session.add(review)
        db.session.commit()

        update_hotel_average_rating(ma_khach_san)

        return True, review
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi thêm đánh giá: {str(e)}"


# =========================================================
# 9. ĐẶT PHÒNG
# =========================================================

def get_booking_by_id(booking_id):
    return DatPhong.query.get(booking_id)


def get_booking_by_code(booking_code):
    return DatPhong.query.filter_by(MaDatPhongCode=booking_code).first()


def get_bookings_by_user(user_id):
    return DatPhong.query.filter_by(MaNguoiDung=user_id).order_by(
        DatPhong.NgayTao.desc()
    ).all()


def generate_booking_code():
    """
    Sinh mã đặt phòng đơn giản theo timestamp.
    """
    return "DP" + datetime.now().strftime("%Y%m%d%H%M%S")


def create_booking(ma_nguoi_dung, ma_khach_san, ngay_nhan_phong,
                   ngay_tra_phong, so_nguoi_luu_tru, chi_tiet_phongs):
    """
    Tạo đơn đặt phòng mới.

    chi_tiet_phongs ví dụ:
    [
        {
            "MaLoaiPhong": 1,
            "SoLuongPhongDat": 1,
            "DonGiaMoiDem": 800000,
            "SoDem": 2,
            "ThanhTien": 1600000
        }
    ]
    """
    ma_dat_phong_code = generate_booking_code()

    while get_booking_by_code(ma_dat_phong_code):
        ma_dat_phong_code = generate_booking_code()

    tong_tien = Decimal("0")

    for item in chi_tiet_phongs:
        tong_tien += Decimal(str(item["ThanhTien"]))

    booking = DatPhong(
        MaDatPhongCode=ma_dat_phong_code,
        MaNguoiDung=ma_nguoi_dung,
        MaKhachSan=ma_khach_san,
        NgayNhanPhong=ngay_nhan_phong,
        NgayTraPhong=ngay_tra_phong,
        SoNguoiLuuTru=so_nguoi_luu_tru,
        TongTien=tong_tien,
        TrangThaiDatPhong=0
    )

    try:
        db.session.add(booking)
        db.session.flush()

        for item in chi_tiet_phongs:
            detail = ChiTietDatPhong(
                MaDatPhong=booking.MaDatPhong,
                MaLoaiPhong=item["MaLoaiPhong"],
                SoLuongPhongDat=item["SoLuongPhongDat"],
                DonGiaMoiDem=item["DonGiaMoiDem"],
                SoDem=item["SoDem"],
                ThanhTien=item["ThanhTien"]
            )
            db.session.add(detail)

        db.session.commit()
        return True, booking
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo đơn đặt phòng: {str(e)}"


def cancel_booking(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking:
        return False, "Không tìm thấy đơn đặt phòng"

    booking.TrangThaiDatPhong = 2

    try:
        db.session.commit()
        return True, booking
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi hủy đơn: {str(e)}"


def complete_booking(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking:
        return False, "Không tìm thấy đơn đặt phòng"

    booking.TrangThaiDatPhong = 3

    try:
        db.session.commit()
        return True, booking
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật hoàn thành đơn: {str(e)}"


# =========================================================
# 10. THANH TOÁN
# =========================================================

def get_payment_by_booking_id(booking_id):
    return ThanhToan.query.filter_by(MaDatPhong=booking_id).first()


def create_payment(ma_dat_phong, phuong_thuc_thanh_toan,
                   trang_thai_thanh_toan, so_tien_thanh_toan,
                   ma_giao_dich=None, thoi_gian_thanh_toan=None):
    """
    Tạo thanh toán cho đơn.
    """
    existing_payment = get_payment_by_booking_id(ma_dat_phong)
    if existing_payment:
        return False, "Đơn đặt phòng này đã có thanh toán"

    payment = ThanhToan(
        MaDatPhong=ma_dat_phong,
        PhuongThucThanhToan=phuong_thuc_thanh_toan,
        TrangThaiThanhToan=trang_thai_thanh_toan,
        SoTienThanhToan=so_tien_thanh_toan,
        MaGiaoDich=ma_giao_dich,
        ThoiGianThanhToan=thoi_gian_thanh_toan
    )

    try:
        db.session.add(payment)

        booking = get_booking_by_id(ma_dat_phong)
        if booking and trang_thai_thanh_toan == 1:
            booking.TrangThaiDatPhong = 1

        db.session.commit()
        return True, payment
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo thanh toán: {str(e)}"


# =========================================================
# 11. HOÀN TIỀN
# =========================================================

def get_refund_by_booking_id(booking_id):
    return HoanTien.query.filter_by(MaDatPhong=booking_id).first()


def create_refund(ma_dat_phong, so_tien_hoan, ly_do_hoan_tien=None,
                  trang_thai_hoan_tien=0, thoi_gian_hoan_tien=None):
    existing_refund = get_refund_by_booking_id(ma_dat_phong)
    if existing_refund:
        return False, "Đơn đặt phòng này đã có bản ghi hoàn tiền"

    refund = HoanTien(
        MaDatPhong=ma_dat_phong,
        SoTienHoan=so_tien_hoan,
        LyDoHoanTien=ly_do_hoan_tien,
        TrangThaiHoanTien=trang_thai_hoan_tien,
        ThoiGianHoanTien=thoi_gian_hoan_tien
    )

    try:
        db.session.add(refund)
        db.session.commit()
        return True, refund
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo hoàn tiền: {str(e)}"


# =========================================================
# 12. CHUYỂN TIỀN CHO KHÁCH SẠN
# =========================================================

def get_transfer_by_booking_id(booking_id):
    return ChuyenTienKhachSan.query.filter_by(MaDatPhong=booking_id).first()


def create_transfer_to_hotel(ma_dat_phong, ma_khach_san, tong_tien_don_hang,
                             phi_he_thong, so_tien_chuyen_cho_khach_san,
                             trang_thai_chuyen_tien=0, thoi_gian_chuyen_tien=None):
    existing_transfer = get_transfer_by_booking_id(ma_dat_phong)
    if existing_transfer:
        return False, "Đơn đặt phòng này đã có bản ghi chuyển tiền"

    transfer = ChuyenTienKhachSan(
        MaDatPhong=ma_dat_phong,
        MaKhachSan=ma_khach_san,
        TongTienDonHang=tong_tien_don_hang,
        PhiHeThong=phi_he_thong,
        SoTienChuyenChoKhachSan=so_tien_chuyen_cho_khach_san,
        TrangThaiChuyenTien=trang_thai_chuyen_tien,
        ThoiGianChuyenTien=thoi_gian_chuyen_tien
    )

    try:
        db.session.add(transfer)
        db.session.commit()
        return True, transfer
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo chuyển tiền: {str(e)}"


# =========================================================
# 13. HÀM CHO ADMIN
# =========================================================

def get_pending_hotels():
    """
    Lấy danh sách khách sạn chờ duyệt.
    """
    return KhachSan.query.filter_by(TrangThaiDuyet=0).order_by(
        KhachSan.NgayTao.desc()
    ).all()


def get_rejected_hotels():
    return KhachSan.query.filter_by(TrangThaiDuyet=2).order_by(
        KhachSan.NgayTao.desc()
    ).all()


def approve_hotel(hotel_id):
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.TrangThaiDuyet = 1
    hotel.NgayDuyet = datetime.now()
    hotel.LyDoTuChoi = None

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi duyệt khách sạn: {str(e)}"


def reject_hotel(hotel_id, ly_do_tu_choi=None, xoa_anh=True):
    """
    Từ chối khách sạn.
    Nếu xoa_anh=True thì xóa thư mục ảnh của khách sạn và cả loại phòng thuộc khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    try:
        # Xóa ảnh loại phòng
        if xoa_anh:
            for room in hotel.loai_phongs:
                if room.ThuMucAnh:
                    xoa_thu_muc_anh(room.ThuMucAnh)

            # Xóa ảnh khách sạn
            if hotel.ThuMucAnh:
                xoa_thu_muc_anh(hotel.ThuMucAnh)

        hotel.TrangThaiDuyet = 2
        hotel.LyDoTuChoi = ly_do_tu_choi
        hotel.NgayDuyet = None

        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi từ chối khách sạn: {str(e)}"


def suspend_hotel(hotel_id):
    """
    Dừng hoạt động khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.TrangThaiHoatDong = 0

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi dừng hoạt động khách sạn: {str(e)}"


def activate_hotel(hotel_id):
    """
    Kích hoạt lại khách sạn.
    """
    hotel = get_hotel_by_id(hotel_id)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.TrangThaiHoatDong = 1

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi kích hoạt khách sạn: {str(e)}"


# =========================================================
# 14. HÀM HỖ TRỢ TRẢ DỮ LIỆU CHO TEMPLATE
# =========================================================


def build_hotel_card_data(hotel):
    """
    Chuẩn bị dữ liệu 1 khách sạn để render ngoài trang chủ.
    Đồng thời lấy ảnh đầu tiên và debug nếu không hiện ảnh.
    """
    if not hotel:
        return None

    cover_image, image_error = lay_anh_dau_tien_va_loi(hotel.ThuMucAnh)

    min_price = None
    active_rooms = [room for room in hotel.loai_phongs if room.TrangThaiHoatDong == 1]

    if active_rooms:
        min_price = min(room.GiaMoiDem for room in active_rooms)

    return {
        "hotel": hotel,
        "cover_image": cover_image,
        "image_error": image_error,
        "thu_muc_anh": hotel.ThuMucAnh,
        "min_price": min_price,
        "chinh_sach_huy_text": hien_thi_chinh_sach_huy(hotel.ChinhSachHuy),
        "trang_thai_duyet_text": hien_thi_trang_thai_duyet(hotel.TrangThaiDuyet),
        "trang_thai_hoat_dong_text": hien_thi_trang_thai_hoat_dong(hotel.TrangThaiHoatDong),
        "review_count": get_review_count_by_hotel(hotel.MaKhachSan)
    }


def build_room_type_data(room_type):
    if not room_type:
        return None

    return {
        "room_type": room_type,
        "cover_image": get_room_cover_image(room_type),
        "images": get_room_images(room_type),
        "trang_thai_hoat_dong_text": hien_thi_trang_thai_hoat_dong(room_type.TrangThaiHoatDong)
    }


def build_booking_data(booking):
    if not booking:
        return None

    return {
        "booking": booking,
        "trang_thai_dat_phong_text": hien_thi_trang_thai_dat_phong(booking.TrangThaiDatPhong),
        "payment": booking.thanh_toan,
        "refund": booking.hoan_tien,
        "transfer": booking.chuyen_tien_khach_san
    }

def cap_nhat_thu_muc_anh_khach_san(ma_khach_san, thu_muc_anh):
    hotel = get_hotel_by_id(ma_khach_san)
    if not hotel:
        return False, "Không tìm thấy khách sạn"

    hotel.ThuMucAnh = thu_muc_anh
    hotel.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, hotel
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật thư mục ảnh khách sạn: {str(e)}"


def cap_nhat_thu_muc_anh_loai_phong(ma_loai_phong, thu_muc_anh):
    room = get_room_type_by_id(ma_loai_phong)
    if not room:
        return False, "Không tìm thấy loại phòng"

    room.ThuMucAnh = thu_muc_anh
    room.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, room
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật thư mục ảnh loại phòng: {str(e)}"

def get_featured_hotels(limit=None):
    """
    Lấy khách sạn nổi bật:
    - đã duyệt
    - đang hoạt động
    - điểm đánh giá > 9
    """
    query = KhachSan.query.filter(
        KhachSan.TrangThaiDuyet == 1,
        KhachSan.TrangThaiHoatDong == 1,
        KhachSan.DiemDanhGiaTrungBinh > 9
    ).order_by(
        KhachSan.DiemDanhGiaTrungBinh.desc(),
        KhachSan.NgayTao.desc()
    )

    if limit:
        return query.limit(limit).all()

    return query.all()

#Chinhsua------------------------
def update_user(user_id, ho_ten, so_dien_thoai, email, so_tai_khoan_ngan_hang):
    user = get_user_by_id(user_id)
    if not user:
        return False, "Không tìm thấy người dùng"

    # Kiểm tra email trùng với người khác
    existing = NguoiDung.query.filter(
        NguoiDung.Email == email,
        NguoiDung.MaNguoiDung != user_id
    ).first()
    if existing:
        return False, "Email đã được sử dụng bởi tài khoản khác"

    user.HoTen = ho_ten
    user.SoDienThoai = so_dien_thoai
    user.Email = email
    user.SoTaiKhoanNganHang = so_tai_khoan_ngan_hang
    user.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, user
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"


def doi_mat_khau(user_id, mat_khau_cu, mat_khau_moi):
    user = get_user_by_id(user_id)
    if not user:
        return False, "Không tìm thấy người dùng"

    # Kiểm tra mật khẩu cũ
    try:
        if not check_password_hash(user.MatKhau, mat_khau_cu):
            if user.MatKhau != mat_khau_cu:
                return False, "Mật khẩu cũ không đúng"
    except Exception:
        if user.MatKhau != mat_khau_cu:
            return False, "Mật khẩu cũ không đúng"

    user.MatKhau = generate_password_hash(mat_khau_moi)
    user.NgayCapNhat = datetime.now()

    try:
        db.session.commit()
        return True, "Đổi mật khẩu thành công"
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi: {str(e)}"