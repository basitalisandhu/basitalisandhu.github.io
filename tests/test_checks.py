from pathlib import Path

from sitekit import checks

URL = "https://example.org"
KEY = "0123456789abcdef0123456789abcdef"
GOOD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>t</title>'
        '<script type="application/ld+json">{"@context": "https://schema.org", "@type": "Thing"}</script>'
        '</head><body><p id="a"><a href="/">home</a> <a href="#a">a</a></p></body></html>')


def make(tmp_path: Path, **files: str) -> Path:
    for name, text in files.items():
        p = tmp_path / name.replace("__", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return tmp_path


def test_good_page_passes(tmp_path):
    d = make(tmp_path, **{"index.html": GOOD})
    assert checks.check_html(d, URL) == []


def test_unclosed_and_mismatched_tags(tmp_path):
    d = make(tmp_path, **{"index.html": GOOD.replace("</p>", "")})
    problems = checks.check_html(d, URL)
    assert any("closes <p>" in p or "never closed" in p for p in problems)


def test_bad_jsonld_and_scripts(tmp_path):
    bad = GOOD.replace('"@type": "Thing"}', '"@type": "Thing",}')
    d = make(tmp_path, **{"index.html": bad})
    assert any("does not parse" in p for p in checks.check_html(d, URL))
    d2 = make(tmp_path / "x", **{"index.html": GOOD.replace("</head>", "<script>alert(1)</script></head>")})
    assert any("script other than JSON-LD" in p for p in checks.check_html(d2, URL))


def test_broken_internal_link_and_anchor(tmp_path):
    d = make(tmp_path, **{"index.html": GOOD.replace('href="/"', 'href="/missing/"').replace('href="#a"', 'href="#zz"')})
    problems = checks.check_html(d, URL)
    assert any("broken internal link /missing/" in p for p in problems)
    assert any("broken anchor #zz" in p for p in problems)


def test_sitemap_urls_must_exist(tmp_path):
    sm = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          f"<url><loc>{URL}/</loc></url><url><loc>{URL}/gone/</loc></url></urlset>")
    d = make(tmp_path, **{"index.html": GOOD, "sitemap.xml": sm})
    assert checks.check_sitemap(d, URL) == [f"sitemap.xml: {URL}/gone/ has no file"]


def test_llms_links_must_be_pages_here(tmp_path):
    txt = f"# T\n\n- [a]({URL}/)\n- [b]({URL}/nope/)\n- [c](https://github.com/x)\n- [d]({URL}/ext/)\n"
    d = make(tmp_path, **{"index.html": GOOD, "llms.txt": txt})
    problems = checks.check_llms(d, URL, {f"{URL}/ext/"})
    assert len(problems) == 2
    assert "nope" in problems[0] and "github.com" in problems[1]


def test_house_style(tmp_path):
    word = "noosaM"[::-1]
    d = make(tmp_path, **{"a.html": "fine\nan \u2014 dash\nuses GPT-4 here\n" + word + " here\n"})
    problems = checks.check_text(d)
    assert [p.split(":")[1] for p in problems] == ["2", "3", "4"]
    assert "Claude Code" not in " ".join(problems)
    assert checks.check_text(make(tmp_path / "ok", **{"b.txt": "Claude Code skills, MCP servers"})) == []


def test_required_files_and_robots(tmp_path):
    d = make(tmp_path, **{"robots.txt": "User-agent: *\nDisallow: /\n", f"{KEY}.txt": "wrong\n"})
    problems = checks.check_required(d, KEY)
    assert "missing index.html" in problems
    assert "IndexNow key file content does not match its name" in problems
    assert "robots.txt does not name GPTBot" in problems
    assert "robots.txt disallows everything" in problems
