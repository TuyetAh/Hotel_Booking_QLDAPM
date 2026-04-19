
from flask import render_template, request, redirect, url_for, session, flash
from app import create_app
from app.dao import (
    check_login,
    register_user,
    get_all_hotels,
    search_hotels,
    get_hotel_by_id,
    get_hotel_detail_data,
    get_bookings_by_user,
    get_user_by_id
)
from app.dao import get_all_hotels, build_hotel_card_data

app = create_app()

# Khóa bí mật để dùng session, flash
app.secret_key = "hotel_booking_secret_key"


# =========================================================
# TRANG CHỦ
# =========================================================

from app.dao import get_all_hotels, build_hotel_card_data, search_hotels





@app.route("/")
def index():
    """
    Trang chủ:
    - lấy danh sách khách sạn đã duyệt và đang hoạt động
    - truyền xuống template để hiển thị
    """
    hotels = get_all_hotels()
    hotel_cards = [build_hotel_card_data(hotel) for hotel in hotels]
    return render_template("index.html", hotel_cards=hotel_cards)


# =========================================================
# TÌM KIẾM KHÁCH SẠN
# =========================================================

@app.route("/tim-kiem")
def tim_kiem():
    keyword = request.args.get("keyword", "").strip()
    city = request.args.get("city", "").strip()

    hotels = search_hotels(keyword=keyword, city=city)
    hotel_cards = [build_hotel_card_data(hotel) for hotel in hotels]

    return render_template(
        "index.html",
        hotel_cards=hotel_cards,
        keyword=keyword,
        city=city
    )


# =========================================================
# CHI TIẾT KHÁCH SẠN
# =========================================================
@app.route("/khach-san/<int:hotel_id>")
def chi_tiet_khach_san(hotel_id):
    """
    Trang chi tiết khách sạn.
    """
    hotel_data = get_hotel_detail_data(hotel_id)

    if not hotel_data:
        flash("Không tìm thấy khách sạn này.", "error")
        return redirect(url_for("index"))

    return render_template("ChiTietKhachSan.html", data=hotel_data)


# =========================================================
# ĐĂNG KÝ
# =========================================================
@app.route("/dang-ky", methods=["GET", "POST"])
def dang_ky():
    """
    Đăng ký tài khoản khách hàng.
    """
    if request.method == "POST":
        ho_ten = request.form.get("fullname")
        ten_dang_nhap = request.form.get("username")
        mat_khau = request.form.get("password")
        so_dien_thoai = request.form.get("phone")
        email = request.form.get("email")
        so_tai_khoan_ngan_hang = request.form.get("bank_account")

        # Kiểm tra dữ liệu đầu vào cơ bản
        if not ho_ten or not ten_dang_nhap or not mat_khau or not so_dien_thoai or not email:
            return render_template(
                "DangKy.html",
                err_msg="Vui lòng nhập đầy đủ các trường bắt buộc."
            )

        success, result = register_user(
            ten_dang_nhap=ten_dang_nhap,
            mat_khau=mat_khau,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            email=email,
            so_tai_khoan_ngan_hang=so_tai_khoan_ngan_hang,
            vai_tro=2  # mặc định là khách hàng
        )

        if success:
            flash("Đăng ký tài khoản thành công. Bạn hãy đăng nhập nhé.", "success")
            return redirect(url_for("dang_nhap"))
        else:
            return render_template("DangKy.html", err_msg=result)

    return render_template("DangKy.html")


# =========================================================
# ĐĂNG NHẬP
# =========================================================
@app.route("/dang-nhap", methods=["GET", "POST"])
def dang_nhap():
    """
    Đăng nhập hệ thống.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template(
                "DangNhap.html",
                err_msg="Vui lòng nhập tên đăng nhập và mật khẩu."
            )

        user = check_login(username, password)

        if user:
            # Lưu thông tin cơ bản vào session
            session["user_id"] = user.MaNguoiDung
            session["username"] = user.TenDangNhap
            session["ho_ten"] = user.HoTen
            session["vai_tro"] = user.VaiTro

            flash("Đăng nhập thành công.", "success")
            return redirect(url_for("index"))
        else:
            return render_template(
                "DangNhap.html",
                err_msg="Sai tên đăng nhập hoặc mật khẩu."
            )

    return render_template("DangNhap.html")


# =========================================================
# ĐĂNG XUẤT
# =========================================================
@app.route("/dang-xuat")
def dang_xuat():
    """
    Xóa session khi đăng xuất.
    """
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("index"))


# =========================================================
# TRANG CÁ NHÂN / ĐƠN ĐẶT PHÒNG CỦA TÔI
# =========================================================
@app.route("/dat-phong-cua-toi")
def dat_phong_cua_toi():
    """
    Hiển thị các đơn đặt phòng của người dùng đang đăng nhập.
    """
    user_id = session.get("user_id")

    if not user_id:
        flash("Bạn cần đăng nhập để xem đơn đặt phòng.", "error")
        return redirect(url_for("dang_nhap"))

    bookings = get_bookings_by_user(user_id)
    return render_template("DatPhongCuaToi.html", bookings=bookings)


# =========================================================
# HÀM HỖ TRỢ: LẤY USER HIỆN TẠI
# =========================================================
@app.context_processor
def inject_user():
    """
    Hàm này giúp mọi template đều có thể dùng biến current_user.
    """
    user_id = session.get("user_id")
    current_user = None

    if user_id:
        current_user = get_user_by_id(user_id)

    return dict(current_user=current_user)




if __name__ == "__main__":
    app.run(debug=True)
