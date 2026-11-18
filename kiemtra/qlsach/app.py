import os
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import ForeignKey, String, event, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 1. CẤU HÌNH FLASK + SQLITE


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "chi-dung-cho-phat-trien-thay-doi-khi-trien-khai"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///quanly_sach.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
csrf.init_app(app)


# Bật kiểm tra khóa ngoại trong SQLite
@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# 2. MODEL DANH MỤC


class Category(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="category")


# 3. MODEL SÁCH


class Book(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    author: Mapped[str] = mapped_column(String(150), nullable=False)

    price: Mapped[float] = mapped_column(default=0.0, nullable=False)

    quantity: Mapped[int] = mapped_column(default=0, nullable=False)

    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)

    category: Mapped[Category] = relationship(back_populates="books")


# Tự tạo bảng nếu chưa tồn tại
with app.app_context():
    db.create_all()


# 4. HÀM HỖ TRỢ


@app.template_filter("vnd")
def format_vnd(value):
    return f"{value:,.0f}".replace(",", ".") + " đ"


def category_name_exists(name, exclude_id=None):
    stmt = select(Category).where(func.lower(Category.name) == name.lower())

    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)

    return db.session.scalar(stmt) is not None


def validate_book_form(form):
    title = form.get("title", "").strip()
    author = form.get("author", "").strip()

    try:
        price = float(form.get("price", ""))
        quantity = int(form.get("quantity", ""))
        category_id = int(form.get("category_id", ""))
    except (ValueError, TypeError):
        return None, "Giá, số lượng hoặc danh mục không hợp lệ."

    if not title or not author:
        return None, "Tên sách và tác giả không được để trống."

    if len(title) > 200 or len(author) > 150:
        return None, "Tên sách hoặc tên tác giả quá dài."

    if not (0 <= price <= 1_000_000_000_000):
        return None, "Giá phải từ 0 đến 1.000.000.000.000."

    if not (0 <= quantity <= 1_000_000_000):
        return None, "Số lượng phải là số nguyên từ 0 đến 1.000.000.000."

    if db.session.get(Category, category_id) is None:
        return None, "Danh mục đã chọn không tồn tại."

    return dict(
        title=title,
        author=author,
        price=price,
        quantity=quantity,
        category_id=category_id,
    ), None


# 5. DASHBOARD


@app.get("/")
def dashboard():
    total_categories = db.session.scalar(select(func.count(Category.id))) or 0

    total_books = db.session.scalar(select(func.count(Book.id))) or 0

    total_quantity = (
        db.session.scalar(select(func.coalesce(func.sum(Book.quantity), 0))) or 0
    )

    category_stats = db.session.execute(
        select(Category.name, func.count(Book.id).label("book_count"))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    ).all()

    recent_books = db.session.scalars(
        select(Book).order_by(Book.id.desc()).limit(5)
    ).all()

    return render_template(
        "dashboard.html",
        total_categories=total_categories,
        total_books=total_books,
        total_quantity=total_quantity,
        category_stats=category_stats,
        recent_books=recent_books,
    )


# 6. READ DANH MỤC


@app.get("/categories")
def categories():
    rows = db.session.execute(
        select(Category, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id.desc())
    ).all()

    return render_template("categories.html", rows=rows)


# 7. CREATE DANH MỤC


@app.route("/categories/add", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name or len(name) > 100 or len(description) > 500:
            flash(
                "Tên danh mục bắt buộc (tối đa 100 ký tự), mô tả tối đa 500 ký tự.",
                "error",
            )

        elif category_name_exists(name):
            flash("Tên danh mục đã tồn tại.", "error")

        else:
            db.session.add(Category(name=name, description=description))
            db.session.commit()

            flash("Thêm danh mục thành công!", "success")
            return redirect(url_for("categories"))

    return render_template("category_form.html", category=None)


# 8. UPDATE DANH MỤC


@app.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
def edit_category(category_id):
    category = db.get_or_404(Category, category_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name or len(name) > 100 or len(description) > 500:
            flash(
                "Tên danh mục bắt buộc (tối đa 100 ký tự), mô tả tối đa 500 ký tự.",
                "error",
            )

        elif category_name_exists(name, category.id):
            flash("Tên danh mục đã tồn tại.", "error")

        else:
            category.name = name
            category.description = description

            db.session.commit()
            flash("Cập nhật danh mục thành công!", "success")

            return redirect(url_for("categories"))

    return render_template("category_form.html", category=category)


# 9. DELETE DANH MỤC


@app.post("/categories/<int:category_id>/delete")
def delete_category(category_id):
    category = db.get_or_404(Category, category_id)

    has_books = db.session.scalar(
        select(Book.id).where(Book.category_id == category.id).limit(1)
    )

    if has_books is not None:
        flash(
            "Không thể xóa danh mục đang có sách. Hãy chuyển hoặc xóa sách trước.",
            "error",
        )

    else:
        db.session.delete(category)
        db.session.commit()
        flash("Xóa danh mục thành công!", "success")

    return redirect(url_for("categories"))


# 10. READ VÀ LỌC SÁCH


@app.get("/books")
def books():
    category_id = request.args.get("category_id", type=int)

    stmt = select(Book).order_by(Book.id.desc())

    if category_id is not None:
        stmt = stmt.where(Book.category_id == category_id)

    rows = db.session.scalars(stmt).all()

    category_list = db.session.scalars(select(Category).order_by(Category.name)).all()

    return render_template(
        "books.html",
        books=rows,
        categories=category_list,
        selected_category_id=category_id,
    )


# 11. CREATE SÁCH


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    category_list = db.session.scalars(select(Category).order_by(Category.name)).all()

    if not category_list:
        flash("Bạn cần thêm ít nhất một danh mục trước khi thêm sách.", "error")
        return redirect(url_for("add_category"))

    if request.method == "POST":
        data, error = validate_book_form(request.form)

        if error:
            flash(error, "error")

        else:
            db.session.add(Book(**data))
            db.session.commit()

            flash("Thêm sách thành công!", "success")
            return redirect(url_for("books"))

    return render_template("book_form.html", book=None, categories=category_list)


# 12. UPDATE SÁCH


@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.get_or_404(Book, book_id)

    category_list = db.session.scalars(select(Category).order_by(Category.name)).all()

    if request.method == "POST":
        data, error = validate_book_form(request.form)

        if error:
            flash(error, "error")

        else:
            for field, value in data.items():
                setattr(book, field, value)

            db.session.commit()

            flash("Cập nhật sách thành công!", "success")
            return redirect(url_for("books"))

    return render_template("book_form.html", book=book, categories=category_list)


# 13. DELETE SÁCH


@app.post("/books/<int:book_id>/delete")
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)

    db.session.delete(book)
    db.session.commit()

    flash("Xóa sách thành công!", "success")
    return redirect(url_for("books"))


if __name__ == "__main__":
    app.run(debug=True)
