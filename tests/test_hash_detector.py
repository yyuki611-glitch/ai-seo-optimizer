from crawler.hash_detector import generate_hash, detect_status


def test_generate_hash_is_consistent():
    assert generate_hash("テキスト") == generate_hash("テキスト")


def test_generate_hash_normalizes_whitespace():
    assert generate_hash("本文  テキスト\n\nサンプル") == generate_hash("本文 テキスト サンプル")


def test_detect_status_new_when_no_existing_hash():
    assert detect_status("abc123", None) == "new"


def test_detect_status_unchanged_when_same():
    assert detect_status("abc123", "abc123") == "unchanged"


def test_detect_status_updated_when_different():
    assert detect_status("abc123", "xyz789") == "updated"
