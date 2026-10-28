from datetime import datetime
import math
from flask import Flask, render_template, request, abort

app = Flask(__name__)

# --- DỮ LIỆU BÀI 1 ---
SHOP = {
    "name": "Cà phê Sông Hương",
    "address": "12 Lê Lợi, Huế",
    "phone": "0234 3888 999",  # Thêm số điện thoại # DỮ LIỆU CẬP NHẬT BÀI 3
    "open": 7,
    "close": 22,
}

PROMOTIONS = ["Giảm 10% cho sinh viên", "Mua 2 tặng 1 vào thứ Hai"]

# Danh sách 7 món theo đúng test case đề bài
MENU = [
    {
        "id": 1,
        "name": "cà phê đen",
        "price": 20000,
        "available": True,
        "image": "ca-phe-den.jpg",
    },
    {
        "id": 2,
        "name": "bạc xỉu",
        "price": 30000,
        "available": False,
        "image": "bac-xiu.jpg",
    },
    {
        "id": 3,
        "name": "cà phê sữa",
        "price": 25000,
        "available": True,
        "image": "ca-phe-sua.jpg",
    },
    {
        "id": 4,
        "name": "trà đào",
        "price": 35000,
        "available": True,
        "image": "tra-dao.jpg",
    },
    {
        "id": 5,
        "name": "trà sữa",
        "price": 30000,
        "available": True,
        "image": "tra-sua.jpg",
    },
    {
        "id": 6,
        "name": "nước cam",
        "price": 25000,
        "available": True,
        "image": "nuoc-cam.jpg",
    },
    {
        "id": 7,
        "name": "sinh tố bơ",
        "price": 40000,
        "available": True,
        "image": "sinh-to-bo.jpg",
    },
]


# Filter VND an toàn với biến Undefined/None
@app.template_filter("vnd")
def vnd_filter(value):
    if value is None or str(value) == "Undefined":
        return "0 đ"
    try:
        return f"{float(value):,.0f}".replace(",", ".") + " đ"
    except (ValueError, TypeError):
        return "0 đ"


# 1. Trang chủ
@app.get("/")
def index():
    hour = request.args.get("gio", type=int)  # /?gio=9
    if hour is None:
        hour = datetime.now().hour
    is_open = SHOP["open"] <= hour < SHOP["close"]
    return render_template(
        "index.html", shop=SHOP, hour=hour, is_open=is_open, promotions=PROMOTIONS
    )


# 2. Trang Thực đơn
# Route /menu hỗ trợ tham số ?page=N (mỗi trang 3 món)
@app.get("/menu")
def menu():
    page_param = request.args.get("page", "1")

    try:
        page = int(page_param)
    except ValueError:
        page = 1

    PER_PAGE = 3
    total_items = len(MENU)
    total_pages = math.ceil(total_items / PER_PAGE) if total_items > 0 else 1

    if page < 1 or page > total_pages:
        abort(404)

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    items_on_page = MENU[start:end]

    # Tính toán thêm các chỉ số thống kê (tránh biến bị Undefined)
    avg_price = (
        sum(item["price"] for item in MENU) / total_items if total_items > 0 else 0
    )
    available_count = sum(1 for item in MENU if item["available"])

    return render_template(
        "menu.html",
        menu=items_on_page,
        page=page,
        pages=total_pages,
        total_items=total_items,
        avg_price=avg_price,
        available_count=available_count,
        shop=SHOP,
    )


# 3. Trang Liên hệ
@app.get("/contact")
def contact():
    return render_template("contact.html", shop=SHOP)


# 4. Xử lý trang lỗi 404 khi truy cập đường dẫn không tồn tại
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", shop=SHOP), 404


if __name__ == "__main__":
    app.run(debug=True)
