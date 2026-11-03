from flask import Flask, render_template, request

app = Flask(__name__)


# --- HÀM HỖ TRỢ DÙNG CHUNG BÀI 2 ---
def validate_score(score_str):
    if not score_str or not score_str.strip():
        return None, "Vui lòng nhập một số."
    cleaned = score_str.strip().replace(",", ".")
    try:
        val = float(cleaned)
    except ValueError:
        return None, "Vui lòng nhập một số."
    if val < 0 or val > 10:
        return None, "Điểm phải từ 0 đến 10."
    return val, None


def format_num(val):
    if val == int(val):
        return str(int(val))
    return str(val)


# --- ROUTES ---


@app.get("/")
def index():
    return render_template("index.html")


# --- BÀI 1: MÁY TÍNH CƠ BẢN ---
@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    values = {"a": "", "op": "+", "b": ""}
    errors = {}
    result = None

    if request.method == "POST":
        values["a"] = request.form.get("a", "").strip()
        values["op"] = request.form.get("op", "+").strip()
        values["b"] = request.form.get("b", "").strip()

        if values["op"] not in ["+", "-", "*", "/"]:
            errors["op"] = "Phép toán không hợp lệ."

        val_a = None
        if not values["a"]:
            errors["a"] = "Vui lòng nhập một số."
        else:
            try:
                val_a = float(values["a"].replace(",", "."))
            except ValueError:
                errors["a"] = "Vui lòng nhập một số."

        val_b = None
        if not values["b"]:
            errors["b"] = "Vui lòng nhập một số."
        else:
            try:
                val_b = float(values["b"].replace(",", "."))
            except ValueError:
                errors["b"] = "Vui lòng nhập một số."

        if val_b == 0 and values["op"] == "/":
            errors["b"] = "Không thể chia cho 0."

        if not errors:
            if values["op"] == "+":
                res_val = val_a + val_b
            elif values["op"] == "-":
                res_val = val_a - val_b
            elif values["op"] == "*":
                res_val = val_a * val_b
            elif values["op"] == "/":
                res_val = val_a / val_b

            result = f"{format_num(val_a)} {values['op']} {format_num(val_b)} = {format_num(res_val)}"

    return render_template(
        "calculator.html", values=values, errors=errors, result=result
    )


# --- BÀI 2: TÍNH ĐIỂM HỌC PHẦN ---
@app.route("/grade", methods=["GET", "POST"])
def grade():
    values = {"cc": "", "gk": "", "ck": ""}
    errors = {}
    result = None

    if request.method == "POST":
        values["cc"] = request.form.get("cc", "").strip()
        values["gk"] = request.form.get("gk", "").strip()
        values["ck"] = request.form.get("ck", "").strip()

        cc_val, errors["cc"] = validate_score(values["cc"])
        gk_val, errors["gk"] = validate_score(values["gk"])
        ck_val, errors["ck"] = validate_score(values["ck"])

        errors = {k: v for k, v in errors.items() if v is not None}

        if not errors:
            d_hp = round(cc_val * 0.1 + gk_val * 0.3 + ck_val * 0.6, 1)

            if ck_val < 1.0:
                letter = "F (điểm thi dưới 1)"
            elif d_hp >= 8.5:
                letter = "A"
            elif d_hp >= 7.0:
                letter = "B"
            elif d_hp >= 5.5:
                letter = "C"
            elif d_hp >= 4.0:
                letter = "D"
            else:
                letter = "F"

            result = f"{d_hp} - {letter}"

    return render_template("grade.html", values=values, errors=errors, result=result)


# --- BÀI 3: TÍNH CHỈ SỐ BMI ---
@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    values = {"height": "", "weight": ""}
    errors = {}
    result = None

    if request.method == "POST":
        values["height"] = request.form.get("height", "").strip()
        values["weight"] = request.form.get("weight", "").strip()

        # 1. Kiểm tra Chiều cao (50 - 250 cm)
        h_val = None
        if not values["height"]:
            errors["height"] = "Vui lòng nhập một số."
        else:
            try:
                h_val = float(values["height"].replace(",", "."))
                if 0 < h_val < 50:
                    errors["height"] = (
                        "Giá trị phải từ 50 đến 250. (nhập mét thay vì cm)"
                    )
                elif h_val < 50 or h_val > 250:
                    errors["height"] = "Giá trị phải từ 50 đến 250."
            except ValueError:
                errors["height"] = "Vui lòng nhập một số."

        # 2. Kiểm tra Cân nặng (10 - 300 kg)
        w_val = None
        if not values["weight"]:
            errors["weight"] = "Vui lòng nhập một số."
        else:
            try:
                w_val = float(values["weight"].replace(",", "."))
                if w_val < 10 or w_val > 300:
                    errors["weight"] = "Giá trị phải từ 10 đến 300."
            except ValueError:
                errors["weight"] = "Vui lòng nhập một số."

        # 3. Tính toán BMI nếu không có lỗi
        if not errors:
            h_m = h_val / 100.0  # Đổi cm sang mét
            bmi_val = round(w_val / (h_m**2), 1)

            # Phân loại Châu Á & quy định màu sắc
            if bmi_val < 18.5:
                category = "Thiếu cân"
                color_class = "warning"  # Màu vàng
            elif bmi_val < 23.0:
                category = "Bình thường"
                color_class = "success"  # Màu xanh
            elif bmi_val < 25.0:
                category = "Thừa cân"
                color_class = "warning"  # Màu vàng
            else:
                category = "Béo phì"
                color_class = "danger"  # Màu đỏ

            # Tính khoảng cân nặng lý tưởng (ứng với BMI 18.5 - 22.9)
            w_min = round(18.5 * (h_m**2), 1)
            w_max = round(22.9 * (h_m**2), 1)

            result = {
                "bmi": bmi_val,
                "category": category,
                "color_class": color_class,
                "ideal_weight": f"{w_min} – {w_max} kg",
            }

    return render_template("bmi.html", values=values, errors=errors, result=result)


if __name__ == "__main__":
    app.run(debug=True)
