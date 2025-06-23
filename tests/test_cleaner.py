import sys
import os
import pytest

# 将 src 目录添加到 Python 路径中，以便能够导入 bookmark_cleaner
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from bookmark_cleaner.main import clean_url

@pytest.mark.parametrize("original_url, expected_url", [
    ("http://example.com/path?query=123", "http://example.com/path"),
    ("https://example.com/path#fragment", "https://example.com/path"),
    ("https://example.com/path?query=123#fragment", "https://example.com/path"),
    ("https://example.com/", "https://example.com"),
    ("https://example.com", "https://example.com"),
    ("", ""),
])
def test_clean_url(original_url, expected_url):
    """测试 clean_url 函数是否能正确移除查询参数和锚点"""
    assert clean_url(original_url) == expected_url 