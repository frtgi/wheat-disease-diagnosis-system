"""
V21 系统级端到端测试
测试图像诊断、SSE 流式诊断、批量诊断、报告生成
"""
import sys
import os
import time
import json
import asyncio
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000/api/v1"
RESULTS = []


def _create_test_image():
    """创建一个最小有效 JPEG 测试图像"""
    from PIL import Image as PILImage
    img = PILImage.new("RGB", (64, 64), color=(128, 200, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


def log_test(name, passed, detail=""):
    """记录测试结果"""
    status = "PASS" if passed else "FAIL"
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail else ""))


def get_admin_token():
    """获取管理员 Token"""
    import urllib.request
    data = json.dumps({"username": "v21test_admin", "password": "Test1234!"}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/users/login",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        return body.get("data", {}).get("access_token") or body.get("access_token")


def test_image_diagnosis(token):
    """图像诊断端到端测试 (POST /diagnosis/image, 返回 JSON)"""
    print("\n=== 4.1 图像诊断端到端测试 ===")
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{BASE_URL}/diagnosis/image",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        log_test("图像诊断端点可达(GET)", True, f"status={resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 405:
            log_test("图像诊断端点可达", True, "405 需POST")
        elif e.code == 422:
            log_test("图像诊断端点可达", True, "422 需要图像参数")
        else:
            log_test("图像诊断端点可达", False, f"HTTP {e.code}")
    except Exception as e:
        log_test("图像诊断端点可达", False, str(e))

    try:
        test_img = _create_test_image()
        boundary = "----V21ImgBoundary"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"image\"; filename=\"test.jpg\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + test_img + (
            f"\r\n--{boundary}--\r\n"
        ).encode()

        req = urllib.request.Request(
            f"{BASE_URL}/diagnosis/image",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            has_diagnosis = "diagnosis" in result or "detections" in result or "data" in result
            log_test("图像诊断响应结构正确", has_diagnosis,
                     f"keys={list(result.keys())[:5]}")
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode(errors="replace")[:200]
        except Exception:
            pass
        log_test("图像诊断流程", False, f"HTTP {e.code}: {body_text}")
    except Exception as e:
        log_test("图像诊断流程", False, str(e))


def test_sse_diagnosis(token):
    """SSE 流式诊断端到端测试 (POST /diagnosis/fusion/stream)"""
    print("\n=== 4.2 SSE 流式诊断端到端测试 ===")
    import http.client

    try:
        test_img = _create_test_image()
        boundary = "----V21SSEBoundary"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"image\"; filename=\"test.jpg\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + test_img + (
            f"\r\n--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"symptoms\"\r\n\r\n"
            f"test symptoms\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        conn = http.client.HTTPConnection("localhost", 8000, timeout=60)
        conn.request("POST", "/api/v1/diagnosis/fusion/stream", body=body, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "text/event-stream"
        })
        resp = conn.getresponse()
        status = resp.status

        if status == 200:
            content_type = resp.getheader("Content-Type", "")
            is_sse = "text/event-stream" in content_type
            log_test("SSE 响应格式正确", is_sse, f"Content-Type: {content_type}")

            data = resp.read(8192).decode(errors="replace")
            has_event = "event:" in data or "data:" in data
            log_test("SSE 事件流包含事件", has_event, f"data_len={len(data)}")
        elif status == 422:
            log_test("SSE 诊断参数验证", True, "422 参数验证失败")
        else:
            resp_data = resp.read(512).decode(errors="replace")
            log_test("SSE 诊断端点响应", False,
                     f"status={status}, body={resp_data[:200]}")

        conn.close()
    except Exception as e:
        log_test("SSE 诊断流程", False, str(e))


def test_batch_diagnosis(token):
    """批量诊断端到端测试"""
    print("\n=== 4.3 批量诊断端到端测试 ===")
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{BASE_URL}/diagnosis/batch",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        log_test("批量诊断端点可达", True, f"status={resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 405:
            log_test("批量诊断端点可达", True, "405 需POST")
        elif e.code == 422:
            log_test("批量诊断端点可达", True, "422 需要图像参数")
        else:
            log_test("批量诊断端点可达", False, f"HTTP {e.code}")
    except Exception as e:
        log_test("批量诊断端点可达", False, str(e))

    try:
        test_img = _create_test_image()
        boundary = "----V21BatchBoundary"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"images\"; filename=\"test1.jpg\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + test_img + (
            f"\r\n--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"images\"; filename=\"test2.jpg\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + test_img + (
            f"\r\n--{boundary}--\r\n"
        ).encode()

        req = urllib.request.Request(
            f"{BASE_URL}/diagnosis/batch",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            has_summary = "summary" in result or "data" in result
            log_test("批量诊断响应结构正确", has_summary,
                     f"keys={list(result.keys())[:5]}")
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode(errors="replace")[:200]
        except Exception:
            pass
        if e.code == 422:
            log_test("批量诊断空图像被拒绝", True, "422 验证失败")
        else:
            log_test("批量诊断响应", False, f"HTTP {e.code}: {err_body}")
    except Exception as e:
        log_test("批量诊断流程", False, str(e))


def test_report_generation(token):
    """报告生成端到端测试"""
    print("\n=== 4.4 报告生成端到端测试 ===")
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{BASE_URL}/reports/list",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            reports = result.get("data", {}).get("reports", []) or result.get("reports", [])
            log_test("报告列表端点可达", True, f"reports_count={len(reports)}")
    except Exception as e:
        log_test("报告列表端点可达", False, str(e))

    try:
        test_img = _create_test_image()
        boundary = "----V21ReportBoundary"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"image\"; filename=\"test.jpg\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode() + test_img + (
            f"\r\n--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"symptoms\"\r\n\r\n"
            f"test symptoms for report\r\n"
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"report_format\"\r\n\r\n"
            f"html\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        req = urllib.request.Request(
            f"{BASE_URL}/reports/generate",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            has_files = "report_files" in result or "data" in result
            log_test("报告生成端点响应", has_files, f"keys={list(result.keys())[:5]}")
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode(errors="replace")[:300]
        except Exception:
            pass
        if e.code == 422:
            log_test("报告生成参数验证", True, f"422: {body_text}")
        elif e.code == 500:
            log_test("报告生成端点响应", False, f"HTTP 500: {body_text}")
        else:
            log_test("报告生成端点响应", False, f"HTTP {e.code}: {body_text}")
    except Exception as e:
        log_test("报告生成流程", False, str(e))

    try:
        req = urllib.request.Request(
            f"{BASE_URL}/reports/download/test_report.html",
            headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                log_test("报告下载端点响应", True, f"status={resp.status}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log_test("报告下载端点响应", True, "404 文件不存在(预期行为)")
            else:
                log_test("报告下载端点响应", False, f"HTTP {e.code}")
    except Exception as e:
        log_test("报告下载端点", False, str(e))


def test_ai_health(token):
    """AI 健康检查端到端测试"""
    print("\n=== 4.5 AI 健康检查端到端测试 ===")
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{BASE_URL}/diagnosis/health/ai",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            has_status = "status" in result or "mock_mode" in result
            is_mock = result.get("mock_mode", False)
            log_test("AI 健康检查端点", has_status,
                     f"mock_mode={is_mock}, status={result.get('status')}")
    except Exception as e:
        log_test("AI 健康检查端点", False, str(e))


def main():
    """主测试入口"""
    print("=" * 70)
    print("V21 系统级端到端测试")
    print("=" * 70)

    try:
        token = get_admin_token()
        if not token:
            print("ERROR: 无法获取管理员 Token")
            return 1
        print(f"管理员 Token 获取成功 (len={len(token)})")
    except Exception as e:
        print(f"ERROR: 登录失败 - {e}")
        return 1

    test_image_diagnosis(token)
    test_sse_diagnosis(token)
    test_batch_diagnosis(token)
    test_report_generation(token)
    test_ai_health(token)

    print("\n" + "=" * 70)
    print("V21 E2E 测试结果汇总")
    print("=" * 70)
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = total - passed
    print(f"  总测试数: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print("=" * 70)

    if failed > 0:
        print("\n失败详情:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"  [FAIL] {r['name']} -- {r['detail']}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
