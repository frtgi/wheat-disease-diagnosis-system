"""快速端点验证脚本"""
import urllib.request
import json
import io
import sys

BASE = "http://localhost:8000/api/v1"

def create_test_image():
    from PIL import Image as PILImage
    img = PILImage.new("RGB", (64, 64), color=(128, 200, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()

def login():
    data = json.dumps({"username": "v21test_admin", "password": "Test1234!"}).encode()
    req = urllib.request.Request(f"{BASE}/users/login", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        return body.get("data", {}).get("access_token") or body.get("access_token")

def test_endpoint(name, method, path, token, data=None, content_type=None):
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    try:
        req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"  [OK] {name}: status={resp.status}, keys={list(result.keys())[:5]}")
            return True, result
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode(errors="replace")[:150]
        except Exception:
            pass
        print(f"  [FAIL] {name}: HTTP {e.code} - {body_text}")
        return False, None
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return False, None

token = login()
print(f"Token: {token[:20]}...")

print("\n--- Basic Endpoints ---")
test_endpoint("reports/list", "GET", "/reports/list", token)
test_endpoint("health/ai", "GET", "/diagnosis/health/ai", token)
test_endpoint("stats/overview", "GET", "/stats/overview", token)
test_endpoint("diagnosis/records", "GET", "/diagnosis/records", token)

print("\n--- Report Generation ---")
test_img = create_test_image()
boundary = "----QuickTestBoundary"
body = (
    f"--{boundary}\r\n"
    f"Content-Disposition: form-data; name=\"image\"; filename=\"test.jpg\"\r\n"
    f"Content-Type: image/jpeg\r\n\r\n"
).encode() + test_img + (
    f"\r\n--{boundary}\r\n"
    f"Content-Disposition: form-data; name=\"symptoms\"\r\n\r\n"
    f"test symptoms\r\n"
    f"--{boundary}\r\n"
    f"Content-Disposition: form-data; name=\"report_format\"\r\n\r\n"
    f"html\r\n"
    f"--{boundary}--\r\n"
).encode()
test_endpoint("reports/generate", "POST", "/reports/generate", token,
              data=body, content_type=f"multipart/form-data; boundary={boundary}")

print("\n--- Batch Diagnosis ---")
body2 = (
    f"--{boundary}\r\n"
    f"Content-Disposition: form-data; name=\"images\"; filename=\"test.jpg\"\r\n"
    f"Content-Type: image/jpeg\r\n\r\n"
).encode() + test_img + (
    f"\r\n--{boundary}--\r\n"
).encode()
test_endpoint("diagnosis/batch", "POST", "/diagnosis/batch", token,
              data=body2, content_type=f"multipart/form-data; boundary={boundary}")

print("\nDone!")
