# from flask import Flask, request, jsonify, abort, render_template_string
from flask import Flask, request, jsonify, abort, render_template_string, url_for

app = Flask(__name__)

# Dữ liệu mẫu
BOOKS = [
    {
        "id": 1,
        # "title": "Lập trình Python Căn Bản",
        "title": "<script>alert('Hacked XSS!')</script>",
        "author": "Nguyễn Văn A",
        "year": 2023,
        "category": "Lập trình",
        "available": True,
    },
    {
        "id": 2,
        "title": "Flask Web Development",
        "author": "Trần Thị B",
        "year": 2022,
        "category": "Lập trình",
        "available": False,
    },
    {
        "id": 3,
        "title": "Đắc Nhân Tâm",
        "author": "Dale Carnegie",
        "year": 1936,
        "category": "Kỹ năng sống",
        "available": True,
    },
    {
        "id": 4,
        "title": "Kinh Tế Học Vĩ Mô",
        "author": "Lê Văn C",
        "year": 2021,
        "category": "Kinh tế",
        "available": True,
    },
]

# Khung HTML Base mẫu
BASE_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LibraryMS</title>
    <style>
        body { font-family: sans-serif; margin: 20px; line-height: 1.6; }
        nav { background: #eee; padding: 10px; margin-bottom: 20px; }
        nav a { margin-right: 15px; font-weight: bold; text-decoration: none; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        .active { background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; }
    </style>
</head>
<body>
    <nav>
        <a href="{{ url_for('index') }}">Trang chủ</a>
        <a href="{{ url_for('books') }}">Danh sách sách</a>
        <a href="{{ url_for('api_books') }}">API Sách</a>
    </nav>
    {% block content %}{% endblock %}
</body>
</html>
"""


# Route Trang chủ
@app.route("/")
def index():
    total = len(BOOKS)
    available = sum(1 for b in BOOKS if b["available"])
    html = BASE_LAYOUT.replace(
        "{% block content %}{% endblock %}",
        f"""
        <h1>Thống kê Thư viện</h1>
        <p>Tổng số đầu sách: <strong>{total}</strong></p>
        <p>Số sách sẵn sàng cho mượn: <strong>{available}</strong></p>
    """,
    )
    return render_template_string(html)


# Route Danh sách sách + Lọc thể loại
@app.route("/books")
def books():
    category = request.args.get("category", "").strip()
    categories = sorted(list(set(b["category"] for b in BOOKS)))
    filtered = [b for b in BOOKS if b["category"] == category] if category else BOOKS

    cats_html = f'<a href="{ {url_for("books")} }">Tất cả</a> '
    for c in categories:
        cats_html += f'<a href="{{{{ url_for("books", category="{c}") }}}}">{c}</a> '

    rows = ""
    for b in filtered:
        status = (
            "<b style='color:green'>Sẵn sàng</b>"
            if b["available"]
            else "<b style='color:red'>Đã mượn</b>"
        )
        rows += f"""
        <tr>
            <td>{b["id"]}</td>
            <td><a href="{{{{ url_for('book_detail', book_id={b["id"]}) }}}}">{b["title"]}</a></td>
            <td>{b["author"]}</td>
            <td>{b["category"]}</td>
            <td>{status}</td>
        </tr>
        """

    content = f"""
        <h1>Danh sách sách</h1>
        <div style="margin-bottom:15px;">Thể loại: {cats_html}</div>
        <table>
            <tr><th>ID</th><th>Tên sách</th><th>Tác giả</th><th>Thể loại</th><th>Trạng thái</th></tr>
            {rows}
        </table>
    """
    return render_template_string(
        BASE_LAYOUT.replace("{% block content %}{% endblock %}", content)
    )


# Route Chi tiết sách
@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        abort(404, description=f"Không có sách với ID = {book_id}")

    content = f"""
        <h1>Chi tiết sách</h1>
        <p><b>ID:</b> {book["id"]}</p>
        <p><b>Tên sách:</b> {book["title"]}</p>
        <p><b>Tác giả:</b> {book["author"]}</p>
        <p><b>Năm:</b> {book["year"]}</p>
        <p><b>Thể loại:</b> {book["category"]}</p>
        <p><a href="{{{{ url_for('books') }}}}">&larr; Quay lại</a></p>
    """
    return render_template_string(
        BASE_LAYOUT.replace("{% block content %}{% endblock %}", content)
    )


# Route API
@app.route("/api/books")
def api_books():
    return jsonify(BOOKS)


@app.route("/api/books/<int:book_id>")
def api_book_detail(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        return jsonify({"error": f"Không có sách với ID = {book_id}"}), 404
    return jsonify(book)


# Custom 404 cho cả HTML và API
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify(
            {"error": getattr(e, "description", "Không tìm thấy dữ liệu")}
        ), 404

    msg = getattr(e, "description", "Trang không tồn tại")
    content = f"<h2 style='color:red;'>Lỗi 404</h2><p>{msg}</p>"
    return render_template_string(
        BASE_LAYOUT.replace("{% block content %}{% endblock %}", content)
    ), 404


if __name__ == "__main__":
    app.run(debug=True)
