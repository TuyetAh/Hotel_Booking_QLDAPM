from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from app import create_app
from app.dao import (
    check_login,
    register_user,
    get_all_hotels,
    search_hotels,
    get_hotel_by_id,
    get_hotel_detail_data,
    get_bookings_by_user,
    get_user_by_id,
    build_hotel_card_data,
    update_user,
    doi_mat_khau
)

app = create_app()
app.secret_key = "hotel_booking_secret_key"


# =========================================================
# DECORATOR
# =========================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bạn cần đăng nhập để tiếp tục.", "error")
            return redirect(url_for("dang_nhap"))
        return f(*args, **kwargs)
    return decorated_function
def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Bạn cần đăng nhập.", "error")
            return redirect(url_for("dang_nhap"))
        if session.get("vai_tro") != 1:
            flash("Bạn không có quyền truy cập.", "error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# =========================================================
# TRANG CHỦ
# =========================================================
@app.route("/")
def index():
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
    return render_template("index.html", hotel_cards=hotel_cards, keyword=keyword, city=city)


# =========================================================
# CHI TIẾT KHÁCH SẠN
# =========================================================
@app.route("/khach-san/<int:hotel_id>")
def chi_tiet_khach_san(hotel_id):
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
    if request.method == "POST":
        ho_ten = request.form.get("fullname")
        ten_dang_nhap = request.form.get("username")
        mat_khau = request.form.get("password")
        so_dien_thoai = request.form.get("phone")
        email = request.form.get("email")
        so_tai_khoan_ngan_hang = request.form.get("bank_account")

        if not ho_ten or not ten_dang_nhap or not mat_khau or not so_dien_thoai or not email:
            return render_template("DangKy.html",
                                   err_msg="Vui lòng nhập đầy đủ các trường bắt buộc.")

        success, result = register_user(
            ten_dang_nhap=ten_dang_nhap,
            mat_khau=mat_khau,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            email=email,
            so_tai_khoan_ngan_hang=so_tai_khoan_ngan_hang,
            vai_tro=2
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
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("DangNhap.html",
                                   err_msg="Vui lòng nhập tên đăng nhập và mật khẩu.")

        user = check_login(username, password)

        if user:
            session["user_id"] = user.MaNguoiDung
            session["username"] = user.TenDangNhap
            session["ho_ten"] = user.HoTen
            session["vai_tro"] = user.VaiTro
            flash("Đăng nhập thành công.", "success")
            if user.VaiTro == 1:
                return redirect(url_for("chu_khach_san_dashboard"))
            else:
                return redirect(url_for("index"))
        else:
            return render_template("DangNhap.html",
                                   err_msg="Sai tên đăng nhập hoặc mật khẩu.")

    return render_template("DangNhap.html")


# =========================================================
# ĐĂNG XUẤT
# =========================================================
@app.route("/dang-xuat")
def dang_xuat():
    session.clear()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("index"))


# =========================================================
# ĐƠN ĐẶT PHÒNG CỦA TÔI
# =========================================================
@app.route("/dat-phong-cua-toi")
@login_required
def dat_phong_cua_toi():
    bookings = get_bookings_by_user(session.get("user_id"))
    return render_template("DatPhongCuaToi.html", bookings=bookings)


# =========================================================
# INJECT USER CHO MỌI TEMPLATE
# =========================================================
@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    current_user = get_user_by_id(user_id) if user_id else None
    return dict(current_user=current_user)

# =========================================================
# DASHBOARD CHỦ KHÁCH SẠN
# =========================================================
@app.route("/quan-ly")
@owner_required
def chu_khach_san_dashboard():
    return render_template("owner/Dashboard.html")

# =========================================================
# HỒ SƠ CÁ NHÂN
# =========================================================
@app.route("/ho-so")
@login_required
def ho_so():
    user = get_user_by_id(session.get("user_id"))
    bookings = get_bookings_by_user(session.get("user_id"))
    return render_template("HoSo.html", user=user, bookings=bookings)


# =========================================================
# CHỈNH SỬA THÔNG TIN
# =========================================================
@app.route("/chinh-sua-thong-tin", methods=["POST"])
@login_required
def chinh_sua_thong_tin():
    user_id = session.get("user_id")
    ho_ten = request.form.get("ho_ten")
    so_dien_thoai = request.form.get("so_dien_thoai")
    email = request.form.get("email")
    so_tai_khoan_ngan_hang = request.form.get("so_tai_khoan_ngan_hang")

    success, result = update_user(
        user_id=user_id,
        ho_ten=ho_ten,
        so_dien_thoai=so_dien_thoai,
        email=email,
        so_tai_khoan_ngan_hang=so_tai_khoan_ngan_hang
    )

    if success:
        session["ho_ten"] = result.HoTen
        flash("Cập nhật thông tin thành công.", "success")
    else:
        flash(result, "error")

    return redirect(url_for("ho_so"))


# =========================================================
# ĐỔI MẬT KHẨU
# =========================================================
@app.route("/doi-mat-khau", methods=["POST"])
@login_required
def doi_mat_khau_route():
    user_id = session.get("user_id")
    mat_khau_cu = request.form.get("mat_khau_cu")
    mat_khau_moi = request.form.get("mat_khau_moi")
    xac_nhan_mat_khau = request.form.get("xac_nhan_mat_khau")

    if mat_khau_moi != xac_nhan_mat_khau:
        flash("Mật khẩu mới không khớp.", "error")
        return redirect(url_for("ho_so"))

    if len(mat_khau_moi) < 6:
        flash("Mật khẩu mới phải có ít nhất 6 ký tự.", "error")
        return redirect(url_for("ho_so"))

    success, msg = doi_mat_khau(user_id, mat_khau_cu, mat_khau_moi)

    if success:
        flash("Đổi mật khẩu thành công.", "success")
    else:
        flash(msg, "error")

    return redirect(url_for("ho_so"))

if __name__ == "__main__":
    app.run(debug=True)