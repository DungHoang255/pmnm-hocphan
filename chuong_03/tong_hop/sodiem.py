import csv
import io
from markupsafe import escape
from flask import Flask, request, jsonify, redirect, url_for, abort, make_response

app = Flask(__name__)

# Cấu hình JSON hiển thị tiếng Việt có dấu
app.json.ensure_ascii = False

# ==========================================
# CÂU 0.1 - 0.2: DỮ LIỆU MẪU
# ==========================================
STUDENTS = {
    "23T1020001": {
        "name": "Nguyễn Văn An",
        "lop": "K47A",
        "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0},
    },
    "23T1020002": {
        "name": "Trần Thị Bình",
        "lop": "K47A",
        "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0},
    },
    "23T1020003": {
        "name": "Lê Hoàng Cường",
        "lop": "K47B",
        "scores": {"PMMNM": 9.5, "CSDL": 9.0},
    },
    "23T1020004": {
        "name": "Phạm Minh Dũng",
        "lop": "K47B",
        "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0},
    },
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A", "scores": {}},
    "23T1020006": {
        "name": "Võ Quốc Khánh",
        "lop": "K47C",
        "scores": {"PMMNM": 7.5, "MMT": 8.0},
    },
}


# ==========================================
# CÂU 0.3 - 0.4: HÀM PHỤ VÀ KHUNG TRANG
# ==========================================
def average(scores):
    """Tính trung bình cộng các điểm số, làm tròn 2 chữ số. Trả về None nếu dict rỗng."""
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    """Xếp loại dựa trên điểm trung bình."""
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7.0:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"


def student_summary(mssv):
    """Trả về dict thông tin tóm tắt của một sinh viên."""
    student = STUDENTS.get(mssv)
    if not student:
        return None
    avg = average(student["scores"])
    return {
        "mssv": mssv,
        "name": student["name"],
        "lop": student["lop"],
        "scores": student["scores"],
        "average": avg,
        "rank": rank(avg),
    }


def layout(title, body):
    """Khung trang HTML chung với menu điều hướng tự động bằng url_for."""
    title_escaped = escape(title)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title_escaped} - Sổ điểm</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        nav {{ margin-bottom: 20px; padding: 10px; background: #f0f0f0; border-radius: 4px; }}
        nav a {{ margin-right: 15px; text-decoration: none; color: #0066cc; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .filter-bar {{ margin-bottom: 15px; }}
        .filter-bar a {{ margin-right: 10px; text-decoration: none; padding: 4px 8px; border: 1px solid #ccc; border-radius: 3px; }}
        .filter-bar a.active {{ background: #0066cc; color: white; border-color: #0066cc; }}
        .error-box {{ background: #ffe6e6; border: 1px solid #ff9999; padding: 15px; border-radius: 4px; }}
    </style>
</head>
<body>
    <nav>
        <a href="{url_for("index")}">Trang chủ</a> · 
        <a href="{url_for("student_list")}">Sinh viên</a> · 
        <a href="{url_for("search_student")}">Tìm kiếm</a>
    </nav>
    <main>
        {body}
    </main>
</body>
</html>"""


# ==========================================
# PHẦN 1: GIAO DIỆN WEB (CÂU 1 - 6)
# ==========================================


@app.route("/")
def index():
    """Câu 1: Trang chủ - Tổng số sinh viên, số lớp, liên kết đến các trang danh sách và API."""
    total_students = len(STUDENTS)
    unique_classes = len(set(s["lop"] for s in STUDENTS.values()))

    body = f"""
    <h1>Tổng quan hệ thống Sổ điểm</h1>
    <p>Tổng số sinh viên: <strong>{total_students}</strong></p>
    <p>Số lớp học: <strong>{unique_classes}</strong></p>
    <ul>
        <li><a href="{url_for("student_list")}">Xem danh sách sinh viên (Giao diện Web)</a></li>
        <li><a href="{url_for("api_students")}">Xem danh sách sinh viên (API JSON)</a></li>
    </ul>
    """
    return layout("Trang chủ", body)


@app.route("/students")
def student_list():
    """Câu 2: Danh sách sinh viên và lọc theo lớp."""
    lop_filter = request.args.get("lop", "").strip()

    # Lấy danh sách tất cả các lớp (không trùng, sắp xếp tăng dần)
    all_classes = sorted(list(set(s["lop"] for s in STUDENTS.values())))

    # Thanh lọc lớp không viết cứng
    filter_html = ['<div class="filter-bar">Lọc theo lớp: ']
    all_active = 'class="active"' if not lop_filter else ""
    filter_html.append(f'<a href="{url_for("student_list")}" {all_active}>Tất cả</a>')

    for cls in all_classes:
        is_active = 'class="active"' if lop_filter.lower() == cls.lower() else ""
        filter_html.append(
            f'<a href="{url_for("student_list", lop=cls)}" {is_active}>{escape(cls)}</a>'
        )
    filter_html.append("</div>")

    # Lọc danh sách sinh viên (không phân biệt hoa thường)
    filtered_students = []
    for mssv in sorted(STUDENTS.keys()):
        s = STUDENTS[mssv]
        if not lop_filter or s["lop"].lower() == lop_filter.lower():
            filtered_students.append(student_summary(mssv))

    if not filtered_students:
        table_html = "<p>Không có sinh viên phù hợp.</p>"
    else:
        rows = []
        for s in filtered_students:
            avg_str = f"{s['average']:.2f}" if s["average"] is not None else "-"
            detail_url = url_for("student_detail", mssv=s["mssv"])
            rows.append(f"""
            <tr>
                <td><a href="{detail_url}">{escape(s["mssv"])}</a></td>
                <td>{escape(s["name"])}</td>
                <td>{escape(s["lop"])}</td>
                <td>{avg_str}</td>
                <td>{escape(s["rank"])}</td>
            </tr>
            """)

        table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>MSSV</th>
                    <th>Họ tên</th>
                    <th>Lớp</th>
                    <th>Điểm TB</th>
                    <th>Xếp loại</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """

    body = f"<h1>Danh sách sinh viên</h1>{''.join(filter_html)}{table_html}"
    return layout("Danh sách sinh viên", body)


@app.route("/students/<mssv>")
def student_detail(mssv):
    """Câu 3: Chi tiết sinh viên."""
    s = student_summary(mssv)
    if not s:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    avg_str = f"{s['average']:.2f}" if s["average"] is not None else "Chưa có điểm"
    class_url = url_for("student_list", lop=s["lop"])
    export_url = url_for("export_csv", mssv=mssv)
    short_link_url = url_for("student_short_link", mssv=mssv)

    # Bảng điểm từng học phần
    if s["scores"]:
        score_rows = "".join(
            [
                f"<tr><td>{escape(course)}</td><td>{score}</td></tr>"
                for course, score in sorted(s["scores"].items())
            ]
        )
        score_table = f"""
        <table>
            <thead><tr><th>Học phần</th><th>Điểm</th></tr></thead>
            <tbody>{score_rows}</tbody>
        </table>
        """
    else:
        score_table = "<p>Chưa có điểm học phần nào.</p>"

    body = f"""
    <h1>Chi tiết sinh viên: {escape(s["name"])}</h1>
    <p><strong>MSSV:</strong> {escape(s["mssv"])}</p>
    <p><strong>Lớp:</strong> <a href="{class_url}">{escape(s["lop"])}</a></p>
    <p><strong>Điểm TB:</strong> {avg_str}</p>
    <p><strong>Xếp loại:</strong> {escape(s["rank"])}</p>
    <p>
        <a href="{export_url}">Tải bảng điểm (CSV)</a> | 
        Link rút gọn: <a href="{short_link_url}">{short_link_url}</a>
    </p>
    <h2>Bảng điểm chi tiết</h2>
    {score_table}
    """
    return layout(f"Sinh viên {s['name']}", body)


@app.route("/sv/<mssv>")
def student_short_link(mssv):
    """Câu 4: Link rút gọn chuyển hướng tới /students/<mssv> với mã 301."""
    return redirect(url_for("student_detail", mssv=mssv), code=301)


@app.route("/students/<mssv>/export")
def export_csv(mssv):
    """Câu 5: Xuất bảng điểm CSV dùng make_response."""
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    scores = STUDENTS[mssv]["scores"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["hoc_phan", "diem"])
    for course, score in scores.items():
        writer.writerow([course, score])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return response


@app.route("/search")
def search_student():
    """Câu 6: Tìm kiếm an toàn chống XSS."""
    q = request.args.get("q", "").strip()
    q_escaped = escape(q)

    results_html = ""
    if "q" in request.args:
        q_lower = q.lower()
        matches = []
        for mssv in sorted(STUDENTS.keys()):
            s = STUDENTS[mssv]
            if q_lower in mssv.lower() or q_lower in s["name"].lower():
                matches.append(student_summary(mssv))

        results_html += f"<h2>Tìm thấy {len(matches)} kết quả cho “{q_escaped}”</h2>"
        if matches:
            items = []
            for m in matches:
                link = url_for("student_detail", mssv=m["mssv"])
                items.append(
                    f'<li><a href="{link}">{escape(m["mssv"])} - {escape(m["name"])} ({escape(m["lop"])})</a></li>'
                )
            results_html += f"<ul>{''.join(items)}</ul>"
        else:
            results_html += "<p>Không tìm thấy sinh viên nào phù hợp.</p>"

    body = f"""
    <h1>Tìm kiếm sinh viên</h1>
    <form action="{url_for("search_student")}" method="GET">
        <input type="text" name="q" value="{q_escaped}" placeholder="Nhập tên hoặc MSSV..." required>
        <button type="submit">Tìm kiếm</button>
    </form>
    {results_html}
    """
    return layout("Tìm kiếm", body)


# ==========================================
# PHẦN 2: API JSON (CÂU 7 - 8)
# ==========================================


@app.route("/api/students")
def api_students():
    """Câu 7: API đọc danh sách sinh viên (hỗ trợ lọc lop và min_avg)."""
    lop = request.args.get("lop", "").strip()

    # Phân biệt giữa không có tham số min_avg và truyền min_avg sai kiểu
    min_avg = None
    if "min_avg" in request.args:
        try:
            min_avg = float(request.args["min_avg"])
        except ValueError:
            abort(400, description="Tham số min_avg phải là một số thực hợp lệ.")

    results = []
    for mssv in sorted(STUDENTS.keys()):
        summary = student_summary(mssv)

        # Lọc theo lớp
        if lop and summary["lop"].lower() != lop.lower():
            continue

        # Lọc theo min_avg (bỏ qua sinh viên chưa có điểm)
        if min_avg is not None:
            if summary["average"] is None or summary["average"] < min_avg:
                continue

        results.append(summary)

    return jsonify(results)


@app.route("/api/students/<mssv>")
def api_student_detail(mssv):
    """Câu 7: API đọc thông tin 1 sinh viên."""
    summary = student_summary(mssv)
    if not summary:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    return jsonify(summary)


@app.route("/api/students/<mssv>/scores/<course>", methods=["GET", "PUT", "DELETE"])
def api_course_score(mssv, course):
    """Câu 8: Quản lý điểm một học phần (GET, PUT, DELETE)."""
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    course_upper = course.upper()
    student_scores = STUDENTS[mssv]["scores"]

    # 1. GET: Xem điểm
    if request.method == "GET":
        if course_upper not in student_scores:
            abort(404, description=f"Học phần {course_upper} chưa có điểm.")
        return jsonify(
            {
                "mssv": mssv,
                "course": course_upper,
                "score": student_scores[course_upper],
            }
        ), 200

    # 2. PUT: Thêm hoặc sửa điểm
    if request.method == "PUT":
        score_param = request.args.get("score")
        if score_param is None:
            abort(400, description="Thiếu tham số score.")

        try:
            score_val = float(score_param)
        except ValueError:
            abort(400, description="Điểm score phải là số hợp lệ.")

        if not (0 <= score_val <= 10):
            abort(400, description="Điểm score phải nằm trong khoảng [0, 10].")

        is_new = course_upper not in student_scores
        student_scores[course_upper] = score_val
        new_avg = average(student_scores)

        body_data = {
            "mssv": mssv,
            "course": course_upper,
            "score": score_val,
            "average": new_avg,
        }

        if is_new:
            resp = make_response(jsonify(body_data), 201)
            resp.headers["Location"] = url_for(
                "api_course_score", mssv=mssv, course=course_upper
            )
            return resp
        else:
            return jsonify(body_data), 200

    # 3. DELETE: Xoá điểm
    if request.method == "DELETE":
        if course_upper not in student_scores:
            abort(404, description=f"Học phần {course_upper} chưa có điểm để xoá.")
        del student_scores[course_upper]
        return "", 204


# ==========================================
# PHẦN 3: XỬ LÝ LỖI (CÂU 9)
# ==========================================


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    """Câu 9: Trang lỗi thống nhất cho 400, 404, 405."""
    titles = {
        400: "Dữ liệu không hợp lệ",
        404: "Không tìm thấy",
        405: "Phương thức không được hỗ trợ",
    }

    code = getattr(error, "code", 500)
    title = titles.get(code, "Lỗi")
    description = getattr(error, "description", str(error))

    # URL bắt đầu bằng /api/ -> Trả về JSON
    if request.path.startswith("/api/"):
        return jsonify({"error": title, "detail": description}), code

    # URL khác -> Trả về HTML dùng layout()
    body = f"""
    <div class="error-box">
        <h1>{code} - {escape(title)}</h1>
        <p>{escape(description)}</p>
    </div>
    """
    return layout(f"{code} {title}", body), code


if __name__ == "__main__":
    app.run(port=8000, debug=True)
