from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, func

# Đổi tên biến cấu hình Header để tránh đụng độ tên với kiểu TEXT của SQLAlchemy
HEADERS = {"Content-Type": "text/plain; charset=utf-8"}


# 1. Cấu hình kết nối
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-chi-dung-khi-phat-trien"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qlsv.db"
db.init_app(app)


# 2. Khai báo Model
class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"


# 3. Tạo bảng tự động
with app.app_context():
    db.create_all()


# 4. Route thêm dữ liệu mẫu
@app.get("/them-mau")
def add_sample():
    total = db.session.scalar(db.select(func.count(Student.id)))
    if total > 0:
        return f"Đã có {total} sinh viên, không thêm nữa."

    an = Student(mssv="23T1020001", name="Nguyễn Văn An", gpa=8.5)
    before = an.id

    db.session.add(an)
    db.session.add_all(
        [
            Student(mssv="23T1020002", name="Trần Thị Bình", gpa=6.8),
            Student(mssv="23T1020003", name="Lê Hoàng Cường", gpa=9.1),
            Student(mssv="23T1020004", name="Phạm Minh Dũng", gpa=4.5),
            Student(mssv="23T1020005", name="Hoàng Thu Hà", gpa=7.4),
        ]
    )

    db.session.commit()

    return (
        f"Đã thêm 5 sinh viên. id của An: trước commit = {before}, sau commit = {an.id}"
    )


# 5. Route thử truy vấn
@app.get("/thu-truy-van")
def try_queries():
    if db.session.scalar(db.select(func.count(Student.id))) == 0:
        return "Chưa có dữ liệu, hãy mở /them-mau trước."

    lines = []
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")

    everyone = db.session.execute(db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")

    stmt = db.select(Student).where(Student.gpa >= 8).order_by(Student.gpa.desc())
    good = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 8: {good}")

    binh = db.session.scalar(db.select(Student).filter_by(mssv="23T1020002"))
    lines.append(f"5. MSSV 23T1020002: {binh}")

    count = db.session.scalar(db.select(func.count(Student.id)))
    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")

    # Trả về kết quả kèm HEADERS
    return "\n".join(lines), HEADERS


# 6. Render Template hiển thị bảng danh sách sinh viên
@app.get("/danh-sach")
def list_students():
    # Lấy toàn bộ danh sách sinh viên từ CSDL[cite: 7]
    students = db.session.execute(db.select(Student)).scalars().all()
    # Trả về giao diện students.html và truyền biến students vào template
    return render_template("students.html", students=students)


if __name__ == "__main__":
    app.run(debug=True)
