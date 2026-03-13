from crawler.content_extractor import extract_content

HTML_WITH_JSON_LD = """
<html>
<head>
  <title>テスト記事タイトル</title>
  <script type="application/ld+json">
  {"@type": "Article", "headline": "LD記事タイトル",
   "datePublished": "2024-01-15", "dateModified": "2024-02-01"}
  </script>
</head>
<body>
  <article>
    <h1>メイン見出し</h1>
    <h2>セクション1</h2>
    <p>本文テキスト1です。</p>
    <h2>セクション2</h2>
    <p>本文テキスト2です。</p>
  </article>
</body>
</html>"""

HTML_WITHOUT_JSON_LD = """
<html>
<head><title>シンプルな記事</title></head>
<body>
  <article>
    <h1>記事タイトル</h1>
    <p>本文テキスト。</p>
    <time datetime="2024-03-01">2024年3月1日</time>
  </article>
</body>
</html>"""


def test_extract_content_returns_title_from_title_tag():
    result = extract_content(HTML_WITHOUT_JSON_LD)
    assert result["title"] == "シンプルな記事"


def test_extract_content_returns_body_text():
    result = extract_content(HTML_WITH_JSON_LD)
    assert "本文テキスト1" in result["body_text"]
    assert "本文テキスト2" in result["body_text"]


def test_extract_content_returns_headings():
    result = extract_content(HTML_WITH_JSON_LD)
    headings = result["heading_structure"]
    assert any(h["text"] == "メイン見出し" and h["level"] == 1 for h in headings)
    assert any(h["text"] == "セクション1" and h["level"] == 2 for h in headings)


def test_extract_content_prefers_json_ld_date():
    result = extract_content(HTML_WITH_JSON_LD)
    assert result["published_at"] == "2024-01-15"
    assert result["updated_at"] == "2024-02-01"


def test_extract_content_falls_back_to_time_tag():
    result = extract_content(HTML_WITHOUT_JSON_LD)
    assert result["published_at"] == "2024-03-01"


def test_extract_content_returns_none_for_missing_date():
    html = "<html><body><p>日付なし</p></body></html>"
    result = extract_content(html)
    assert result["published_at"] is None
