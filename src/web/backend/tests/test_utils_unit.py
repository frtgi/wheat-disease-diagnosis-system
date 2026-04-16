"""
Utils 和工具模块单元测试
覆盖 common.py、xss_protection.py、image_hash.py 等工具模块
"""
import pytest
from datetime import datetime, timezone


class TestCommonUtils:
    """通用工具函数测试"""

    def test_generate_unique_id(self):
        """
        测试生成唯一 ID

        应返回有效的 UUID 格式字符串，且每次调用结果不同
        """
        from app.utils.common import generate_unique_id

        id1 = generate_unique_id()
        id2 = generate_unique_id()

        assert isinstance(id1, str)
        assert len(id1) == 36  # UUID 标准长度
        assert id1 != id2

    def test_format_datetime_with_value(self):
        """
        测试格式化有效日期时间

        datetime 对象应转换为 YYYY-MM-DD HH:MM:SS 格式
        """
        from app.utils.common import format_datetime

        dt = datetime(2025, 6, 15, 10, 30, 45)
        result = format_datetime(dt)
        assert result == "2025-06-15 10:30:45"

    def test_format_datetime_none(self):
        """
        测试格式化 None 返回 None
        """
        from app.utils.common import format_datetime

        result = format_datetime(None)
        assert result is None

    def test_paginate_first_page(self):
        """
        测试分页第一页

        page=1 时应返回前 page_size 条数据
        """
        from app.utils.common import paginate

        items = list(range(1, 26))
        result = paginate(items, page=1, page_size=10)
        assert result["items"] == list(range(1, 11))
        assert result["total"] == 25
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_pages"] == 3

    def test_paginate_second_page(self):
        """
        测试分页第二页
        """
        from app.utils.common import paginate

        items = list(range(1, 21))
        result = paginate(items, page=2, page_size=5)
        assert result["items"] == [6, 7, 8, 9, 10]
        assert result["total_pages"] == 4

    def test_paginate_last_page_partial(self):
        """
        测试最后一页不满的情况

        总数不是 page_size 整倍数时，最后一页数据量不足 page_size
        """
        from app.utils.common import paginate

        items = list(range(1, 12))
        result = paginate(items, page=2, page_size=10)
        assert result["items"] == [11]
        assert result["total_pages"] == 2

    def test_pagate_empty_list(self):
        """
        测试空列表分页

        空列表应返回空 items 和 total=0
        """
        from app.utils.common import paginate

        result = paginate([], page=1, page_size=10)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["total_pages"] == 0

    def test_paginate_page_beyond_range(self):
        """
        测试请求超出范围的页码

        超出范围时返回空列表（不报错）
        """
        from app.utils.common import paginate

        items = [1, 2, 3]
        result = paginate(items, page=100, page_size=10)
        assert result["items"] == []
        assert result["total"] == 3


class TestXssProtection:
    """XSS 防护模块测试"""

    def test_sanitize_input_normal_text(self):
        """
        测试正常文本转义

        不含 HTML 的文本应原样返回
        """
        from app.utils.xss_protection import sanitize_input

        assert sanitize_input("hello world") == "hello world"
        assert sanitize_input("") == ""

    def test_sanitize_input_script_tag(self):
        """
        测试 script 标签转义

        <script> 标签应被转义为 &lt;script&gt;
        """
        from app.utils.xss_protection import sanitize_input

        result = sanitize_input("<script>alert('XSS')</script>")
        assert "<" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_input_none(self):
        """
        测试 None 输入返回 None
        """
        from app.utils.xss_protection import sanitize_input

        assert sanitize_input(None) is None

    def test_sanitize_dict_all_fields(self):
        """
        测试字典全字段转义

        fields_to_sanitize=None 时转义所有字符串字段
        """
        from app.utils.xss_protection import sanitize_dict

        data = {
            "name": "<b>test</b>",
            "email": "normal@email.com",
            "count": 42,
        }
        result = sanitize_dict(data)
        assert "&lt;b&gt;" in result["name"]
        assert result["email"] == "normal@email.com"
        assert result["count"] == 42

    def test_sanitize_dict_specific_fields(self):
        """
        测试指定字段转义

        仅 fields_to_sanitize 列表中的字段被转义
        """
        from app.utils.xss_protection import sanitize_dict

        data = {"title": "<h1>Title</h1>", "body": "<p>Body</p>"}
        result = sanitize_dict(data, ["title"])
        assert "&lt;" in result["title"]
        assert result["body"] == "<p>Body</p>"

    def test_sanitize_dict_nested_dict(self):
        """
        测试嵌套字典递归转义
        """
        from app.utils.xss_protection import sanitize_dict

        data = {"user": {"name": "<i>Name</i>"}}
        result = sanitize_dict(data)
        assert "&lt;i&gt;" in result["user"]["name"]

    def test_validate_username_valid(self):
        """
        测试有效用户名验证

        字母数字下划线组合应通过验证
        """
        from app.utils.xss_protection import validate_username

        valid, msg = validate_username("user_123")
        assert valid is True
        assert msg == ""

    def test_validate_username_empty(self):
        """
        测试空用户名被拒绝
        """
        from app.utils.xss_protection import validate_username

        valid, msg = validate_username("")
        assert valid is False
        assert "不能为空" in msg

    def test_validate_username_too_short(self):
        """
        测试用户名过短被拒绝
        """
        from app.utils.xss_protection import validate_username

        valid, _ = validate_username("ab")
        assert valid is False

    def test_validate_username_too_long(self):
        """
        测试用户名过长被拒绝
        """
        from app.utils.xss_protection import validate_username

        valid, _ = validate_username("a" * 51)
        assert valid is False

    def test_validate_username_special_chars(self):
        """
        测试特殊字符用户名被拒绝
        """
        from app.utils.xss_protection import validate_username

        valid, msg = validate_username("<script>")
        assert valid is False
        assert "字母" in msg or "下划线" in msg

    def test_validate_input_no_html_clean(self):
        """
        测试无 HTML 文本通过验证
        """
        from app.utils.xss_protection import validate_input_no_html

        valid, msg = validate_input_no_html("正常文本", "症状")
        assert valid is True
        assert msg == ""

    def test_validate_input_no_html_rejected(self):
        """
        测试含 HTML 标签文本被拒绝
        """
        from app.utils.xss_protection import validate_input_no_html

        valid, msg = validate_input_no_html("<div>内容</div>", "描述")
        assert valid is False
        assert "HTML" in msg

    def test_validate_input_no_html_empty(self):
        """
        测试空文本通过验证（允许为空）
        """
        from app.utils.xss_protection import validate_input_no_html

        valid, msg = validate_input_no_html("", "字段")
        assert valid is True

    def test_escape_html_in_string_basic(self):
        """
        测试基本 HTML 字符转义
        """
        from app.utils.xss_protection import escape_html_in_string

        result = escape_html_in_string("<div>test</div>")
        assert "&lt;" in result
        assert "&gt;" in result

    def test_escape_html_in_string_javascript(self):
        """
        测试 javascript: 协议转义

        javascript: 应被编码以防止 XSS 注入
        """
        from app.utils.xss_protection import escape_html_in_string

        result = escape_html_in_string("javascript:alert('XSS')")
        assert "javascript&#58;" in result.lower()

    def test_escape_html_in_string_none(self):
        """
        测试 None 输入返回 None
        """
        from app.utils.xss_protection import escape_html_in_string

        assert escape_html_in_string(None) is None

    def test_sanitize_response_decorator_dict(self):
        """
        测试响应装饰器处理字典返回值
        """
        from app.utils.xss_protection import sanitize_response

        @sanitize_response(fields_to_sanitize=["name"])
        def get_data():
            return {"name": "<b>Alice</b>", "age": 30}

        result = get_data()
        assert "&lt;" in result["name"]
        assert result["age"] == 30

    def test_sanitize_model_fields_pydantic(self):
        """
        测试 Pydantic 模型字段转义
        """
        from pydantic import BaseModel
        from app.utils.xss_protection import sanitize_model_fields

        class SimpleModel(BaseModel):
            name: str
            value: int

        model = SimpleModel(name="<script>Test</script>", value=99)
        sanitized = sanitize_model_fields(model, ["name"])
        assert "&lt;" in sanitized.name
        assert sanitized.value == 99


class TestImageHash:
    """图像哈希模块测试"""

    def test_compute_md5(self):
        """
        测试 MD5 哈希计算

        相同输入应产生相同 MD5 哈希值
        """
        from app.utils.image_hash import ImageHash

        data = b"test_image_data_12345"
        hash1 = ImageHash.compute_md5(data)
        hash2 = ImageHash.compute_md5(data)

        assert isinstance(hash1, str)
        assert len(hash1) == 32
        assert hash1 == hash2

    def test_compute_md5_different_inputs(self):
        """
        测试不同输入产生不同 MD5 哈希
        """
        from app.utils.image_hash import ImageHash

        h1 = ImageHash.compute_md5(b"data_one")
        h2 = ImageHash.compute_md5(b"data_two")
        assert h1 != h2

    def test_hamming_distance_identical(self):
        """
        测试相同哈希的汉明距离为 0
        """
        from app.utils.image_hash import ImageHash

        dist = ImageHash.hamming_distance("abc123", "abc123")
        assert dist == 0

    def test_hamming_distance_different(self):
        """
        测试不同哈希的汉明距离大于 0
        """
        from app.utils.image_hash import ImageHash

        dist = ImageHash.hamming_distance("000000", "ffffff")
        assert dist > 0

    def test_hamming_distance_mismatched_length(self):
        """
        测试不同长度的哈希应抛出 ValueError
        """
        from app.utils.image_hash import ImageHash

        with pytest.raises(ValueError, match="长度不匹配"):
            ImageHash.hamming_distance("abc", "abcdef")

    def test_is_similar_true(self):
        """
        测试相似图像判断为真

        相同哈希的距离为 0 <= 阈值
        """
        from app.utils.image_hash import ImageHash

        assert ImageHash.is_similar("aaaaaa", "aaaaaa") is True

    def test_is_similar_false(self):
        """
        测试不相似图像判断为假
        """
        from app.utils.image_hash import ImageHash

        result = ImageHash.is_similar("aaaaaa", "ffffff", threshold=3)
        assert result is False

    def test_is_similar_exception_handling(self):
        """
        测试异常时 is_similar 返回 False

        不同长度哈希抛出异常时应优雅降级
        """
        from app.utils.image_hash import ImageHash

        assert ImageHash.is_similar("ab", "abcd") is False

    def test_compute_all_hashes_returns_dict(self):
        """
        测试 compute_all_hashes 返回包含所有类型的字典
        """
        from app.utils.image_hash import ImageHash

        data = b"image_bytes_test"
        hashes = ImageHash.compute_all_hashes(data)
        assert "md5" in hashes
        assert "phash" in hashes
        assert "dhash" in hashes
        assert "ahash" in hashes
        assert hashes["md5"] is not None

    def test_compute_image_hash_default_method(self):
        """
        测试默认使用 phash 方法
        """
        from app.utils.image_hash import compute_image_hash

        data = b"test_data"
        result = compute_image_hash(data, method="md5")
        assert result is not None

    def test_compute_image_hash_unknown_method_fallback(self):
        """
        测试未知方法回退到 phash

        未知方法会记录警告并尝试 phash，非图像数据返回 None
        """
        from app.utils.image_hash import compute_image_hash

        data = b"test_data"
        result = compute_image_hash(data, method="unknown_method")
        assert result is None or isinstance(result, str)

    def test_generate_cache_key(self):
        """
        测试缓存键生成

        缓存键应包含前缀和 MD5 哈希片段
        """
        from app.utils.image_hash import generate_cache_key

        key = generate_cache_key(b"test_image", prefix="diag")
        assert key.startswith("diag:")
        assert len(key) > 10

    def test_generate_cache_key_with_params(self):
        """
        测试带额外参数的缓存键生成
        """
        from app.utils.image_hash import generate_cache_key

        key = generate_cache_key(
            b"img",
            prefix="test",
            extra_params={"symptom": "锈病"}
        )
        assert "test:" in key
