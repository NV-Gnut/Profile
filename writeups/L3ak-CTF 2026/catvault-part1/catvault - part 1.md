# Tổng quan
Tác giả: sy1vi3\
Mô tả: Just cat the flag, as the kids say.\
Nhận xét: 
- Challenge cung cấp các endpoint như `/login` `/register` `/logout` `/vault` `/api/settings`. 
- flag.txt chỉ có root có thể đọc.
- FLAG được tạo ra bởi từ file readflag.c và được lưu vào table 'vault' ở column `content` với user là admin\
```python
def create_admin():
    connect()
    cursor.execute("INSERT INTO users (name, password) VALUES ('admin', 'nologin');")
    conn.commit()
    cursor.execute(f"INSERT INTO vault (user_id, content) VALUES ({cursor.lastrowid}, '{FLAG}');")
    conn.commit()
```
# Phân tích
Dự đoán đầu tiên của mình là dòng chứa flag sẽ nằm ở bảng `vault` có `user_id= 1` or `user_id=0`. Mình sẽ phân tích từng endpoint xem liệu có endpoint nào tác động đến bảng vault hay không .\ 
/login và /register
```python
def create_user(username, password):
    connect()
    cursor.execute("INSERT INTO users (name, password) VALUES (?, ?);", (username, sha256(password).digest().hex()))
    conn.commit()
    return cursor.lastrowid

def login(username, password):
    connect()
    cursor.execute("SELECT id, name, password FROM users WHERE name = ? AND password = ?;", (username, sha256(password).digest().hex()))
```
2 endpoints này đều gọi các hàm `create_user` và `login` để đăng kí và đăng nhập tài khoản. Mình thấy có sử dụng prepared statement('?') thay vì nối chuỗi để chặn `SQL Injection`=> loại

/vault:
```python
@app.route("/vault", methods=["GET", "POST"])
def vault():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        content = (request.form.get("content") or "").strip()
        if not content:
            flash("yap a bit more please", "error")
        elif len(content) > 2000:
            flash("didnt ask", "error")
        else:
            db.add_vault_entry(session["user_id"], content)
            flash("secret saved", "ok")
        return redirect(url_for("vault"))

    try:
        entries = db.get_vault_entries(session["user_id"])
    except mariadb.Error:
        entries = []
        flash("there's been a pawblem...", "error")

    return render_template(
        "vault.html",
        entries=entries,
        username=session.get("username", "cat"),
        theme=session.get("theme", "light"),
    )
```
Endpoints trên sử dụng 2 method là `POST` và `GET`. Request `POST` gọi hàm `add_vault_entry` để thêm `content` vào hàng user_id được lấy từ `session["user_id"]` trong table `vault`. Với req này có tác động đến table `vault` nhưng không thể sql injection vì cũng sử dụng prepared statement.
```python
def add_vault_entry(user_id, content):
    connect()
    cursor.execute(f"INSERT INTO vault (user_id, content) VALUES ({user_id}, ?);", (content,))
    conn.commit()
    return cursor.lastrowid
```
Khi method request `GET` được gọi. Server sẽ gọi hàm `get_vault_entries(session["user_id"])` để lấy các bản ghi trong table `vault` có `id=user_id`. Vì vậy kết quả trả về luôn chỉ là 1 bản ghi => `/vault` với method `GET` sẽ được sử dụng để đọc kết quả và mục tiêu tiếp theo là làm thế nào để tạo ra được session của admin.\
`/api/settings`
```python
@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        abort(401)

    if request.method == "GET":
        prefs = {k: session.get(k, v) for k, v in DEFAULT_PREFS.items()}
        return jsonify(prefs)

    incoming = request.get_json(silent=True)
    if not isinstance(incoming, dict):
        abort(400)

    saved = {}
    for key, value in incoming.items():
        if not isinstance(key, str) or key.startswith("_") or not isinstance(value, str):
            continue
        session[key] = value
        saved[key] = value

    return jsonify({"ok": True, "saved": saved})

``` 
Đối với method `GET` được gọi sẽ sử dụng để thay đổi theme. Nhưng method `POST` sẽ cho phép tạo `session` với `key:value` mình có thể đưa vào => Giả mạo session của admin

# Quá trình khai thác 
1. Tạo một tài khoản ngẫu nhiên và truy cập /api/settings với method `POST` và 2 key `"user_id:1" và "username:admin"`. Response sẽ trả về session mới

![](image.png)

2. Sử dụng session vừa tạo để truy cập `/vault` với method `GET` để lấy FLAG

![](image-1.png)
# FLAG
FLAG: ~~`L3AK{1t_W45_a_v3RY_e45Y_WeB_CH4l1eNge_s0Rry_7o_boRe_YoU_41l_witH_tH3_dUMB_PR3t3xt_N0w_g0_5o1Ve_tH3_Real_0ne}`~~
