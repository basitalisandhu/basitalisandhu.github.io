from sitekit import markdown as md


def test_headings_with_ids_and_offset():
    assert md.convert("# Hello World") == '<h1 id="hello-world">Hello World</h1>'
    assert md.convert("## Two", heading_offset=1) == '<h3 id="two">Two</h3>'
    assert md.convert("###### Six", heading_offset=3).startswith("<h6")
    assert md.convert("# x", heading_ids=False) == "<h1>x</h1>"


def test_paragraphs_join_lines_and_split_on_blank():
    assert md.convert("a\nb\n\nc") == "<p>a b</p>\n<p>c</p>"


def test_lists():
    assert md.convert("- one\n- two") == "<ul><li>one</li><li>two</li></ul>"
    assert md.convert("1. one\n2. two") == "<ol><li>one</li><li>two</li></ol>"
    assert md.convert("- one\n  more\n- two") == "<ul><li>one more</li><li>two</li></ul>"


def test_code_block_is_escaped_and_keeps_language():
    out = md.convert("```python\nprint('<b>')\n```")
    assert out == '<pre><code class="language-python">print(&#x27;&lt;b&gt;&#x27;)</code></pre>'


def test_code_block_keeps_markdown_literal():
    assert "# not a heading" in md.convert("```\n# not a heading\n```")


def test_inline_code_bold_em():
    assert md.inline("`a<b>`") == "<code>a&lt;b&gt;</code>"
    assert md.inline("**bold** and *em*") == "<strong>bold</strong> and <em>em</em>"
    assert md.inline("snake_case_name") == "snake_case_name"


def test_links_and_unsafe_schemes():
    assert md.inline("[x](https://e.org/a?b=1&c=2)") == '<a href="https://e.org/a?b=1&amp;c=2">x</a>'
    assert md.inline("[x](/tool/)") == '<a href="/tool/">x</a>'
    assert md.inline("[bad](javascript:alert(1))") == "bad"
    assert md.inline("<https://e.org>") == '<a href="https://e.org">https://e.org</a>'


def test_images_dropped_and_html_escaped():
    assert md.inline("a ![img](https://e.org/x.png) b") == "a  b"
    assert md.convert("<script>alert(1)</script>") == "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>"


def test_blockquote():
    assert md.convert("> quoted\n> text") == "<blockquote><p>quoted text</p></blockquote>"


def test_front_matter():
    meta, body = md.split_front_matter("---\ntitle: T\ndate: 2026-10-05\n---\nbody\n")
    assert meta == {"title": "T", "date": "2026-10-05"}
    assert body == "body\n"
    assert md.split_front_matter("no front matter") == ({}, "no front matter")


def test_first_paragraph_text():
    assert md.first_paragraph_text("# T\n\nSome [link](x) and `code`.\n\nMore") == "Some link and code."
