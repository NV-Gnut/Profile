# CodeTrace Desktop

CodeTrace là công cụ desktop hỗ trợ kiểm thử source code theo hướng SAST (phân tích
tĩnh). Ứng dụng có thể mở một file hoặc cả thư mục, phát hiện các mẫu nguy hiểm và
hiển thị trace từ nguồn dữ liệu không tin cậy tới sink gây ra lỗ hổng.

## Chức năng

- Mở file hoặc thư mục source code.
- Hỗ trợ Python, JavaScript/TypeScript, PHP và Java.
- Rule tích hợp cho SQL Injection, Command Injection, Path Traversal, XSS,
  Code Injection, Weak Hash và hard-coded secret.
- Trace theo từng finding: source → các bước truyền biến → sink.
- Trace ngược bằng Python AST và Program Dependency Graph: nguồn dữ liệu, tham số,
  phép gán, định nghĩa, nơi đọc, lời gọi và giá trị trả về.
- Code viewer có syntax highlighting cho keyword, chuỗi, số, hàm và comment.
- Tìm kiếm/lọc finding theo loại hoặc mức độ.
- Thêm rule tùy chỉnh bằng JSON ngay trong giao diện.
- Nạp dataset rule JSON với nguồn, CWE và độ tin cậy.
- Xuất báo cáo JSON.

> Đây là công cụ phân tích theo mẫu và data-flow nhẹ, phù hợp để rà soát ban đầu.
> Finding cần được chuyên gia kiểm tra lại; công cụ không thay thế code review hoặc
> các SAST engine chuyên sâu.

## Chạy ứng dụng

Yêu cầu Python 3.10 trở lên (không cần cài package ngoài):

```powershell
python main.py
```

Chạy kiểm thử:

```powershell
python -m unittest discover -s tests -v
```

## Rule tùy chỉnh

Vào **Quản lý rule → Thêm rule**, nhập JSON theo mẫu:

```json
{
  "id": "CUSTOM-SSRF",
  "name": "Server-side request forgery",
  "severity": "HIGH",
  "languages": ["python"],
  "sources": ["request\\.args", "request\\.json"],
  "sinks": ["requests\\.(get|post)\\s*\\("],
  "sanitizers": ["is_safe_url\\s*\\("],
  "message": "Dữ liệu từ request đi vào HTTP client",
  "recommendation": "Chỉ cho phép scheme/host nằm trong allow-list."
}
```

Các trường `sources`, `sinks`, `sanitizers` là biểu thức chính quy. Rule được lưu
tại `%USERPROFILE%/.codetrace/rules.json`.

## AST Reverse Trace

Mở một thư mục source, sau đó bôi đen tên biến/hàm trong code hoặc nhập tên vào ô
**REVERSE TRACE**. Nhấn Enter hoặc **Trace ngược hàm / biến**. Nhấp một kết quả để
đi thẳng tới file và dòng tương ứng.

Với source Python, CodeTrace parse toàn bộ project bằng module `ast`, sau đó dựng
Program Dependency Graph. Ví dụ `FLAG = os.getenv("CTF_FLAG")` tạo chuỗi quan hệ:

```text
SOURCE(os.getenv) → ASSIGNMENT(FLAG) → READ(FLAG)
                  → PARAMETER(value) → ASSIGNMENT(message) → RETURN(reveal)
```

Cửa sổ kết quả mặc định được rút gọn, chỉ giữ các node trả lời trực tiếp ba câu hỏi:
biến được tạo từ đâu, được dùng ở đâu và endpoint nào đi tới nó. Các node AST trung
gian vẫn được engine phân tích nhưng không làm rối sơ đồ.

- **Trace ngắn gọn**: `SOURCE → ASSIGNMENT → READ/CALL` và
  `ENDPOINT → FUNCTION → READ`.
- **Danh sách**: các node quan trọng kèm file, dòng và ý nghĩa.

### Ví dụ cách đọc graph `FLAG`

Với file `examples/flag_demo.py`:

```python
FLAG = os.getenv("CTF_FLAG")

@app.get("/flag")
def get_flag():
    flag_output = format_flag(FLAG)
    return {"flag": flag_output}
```

Sơ đồ được đọc từ trên xuống:

```text
SOURCE os.getenv                  ENDPOINT GET /flag
        │ FLOWS_TO                         │ HANDLES
        ▼                                  ▼
ASSIGNMENT FLAG                  FUNCTION get_flag
        │ READS                            │ CONTAINS
        └──────────────┬───────────────────┘
                       ▼
                  READ FLAG       ← handler đọc FLAG tại đây
        │ ARGUMENT
        ▼
CALL format_flag
        │ PASSES_TO
        ▼
PARAMETER value             ← value nhận cùng dữ liệu với FLAG
        │ FLOWS_TO
        ▼
ASSIGNMENT decorated
        │ RETURNS
        ▼
RETURN format_flag
```

Ý nghĩa các cạnh chính:

- `FLOWS_TO`: dữ liệu từ node trên tạo/cập nhật node dưới.
- `READS`: một vị trí code đọc giá trị của biến.
- `ARGUMENT`: giá trị được đưa vào một lời gọi hàm.
- `PASSES_TO`: đối số ở caller truyền sang parameter của callee.
- `RETURNS`: dữ liệu đi vào giá trị trả về.
- `CALLS`: liên kết định nghĩa hàm với nơi hàm được gọi.
- `IMPORTS`: biến được chuyển qua câu lệnh import giữa hai file.
- `HANDLES`: endpoint được ánh xạ tới handler function.
- `CONTAINS`: thao tác đọc/gán nằm trong handler đó.

Khi nhấp vào một node trên sơ đồ, cửa sổ graph sẽ đóng và CodeTrace đưa code viewer
lên trước, mở đúng file và đánh dấu dòng tương ứng.

Reverse trace AST hiện hỗ trợ Python. JavaScript/TypeScript/PHP/Java vẫn được quét
lỗ hổng theo rule, nhưng ứng dụng sẽ không gắn nhãn AST cho các kết quả đó.

## Dataset và giảm false positive

Dataset tích hợp nằm tại `datasets/security_rules.json`. Mỗi rule có `confidence`,
`cwe` và `dataset_source`. Có thể nạp thêm tại **Quản lý rule → Nhập dataset rule
JSON**; rule trùng ID tự động bị bỏ qua.

Với Python, source-to-sink detection chạy theo AST scope. Taint trong một function
không bị nối nhầm sang sink của function khác và sanitizer sẽ cắt luồng trước sink.
JavaScript/TypeScript/PHP/Java hiện vẫn dùng engine theo dòng nên cần review finding
kỹ hơn.
