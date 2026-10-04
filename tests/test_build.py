import json
import re
from pathlib import Path

import build
from sitekit import checks, site

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"


def run(tmp_path: Path) -> Path:
    out = tmp_path / "docs"
    assert build.main(["--out", str(out), "--data", str(FIX / "repos.json"), "--content", str(FIX / "content")]) == 0
    return out


def jsonld_blocks(html: str) -> list[dict]:
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', html, re.S)]


def test_builds_expected_files(tmp_path):
    out = run(tmp_path)
    for rel in ["index.html", "404.html", ".nojekyll", "robots.txt", "sitemap.xml", "feed.xml", "llms.txt", "llms-full.txt",
                "style.css", "posts/index.html", "posts/hello/index.html", "tool-one/index.html", "tool-two/index.html"]:
        assert (out / rel).is_file(), rel
    key = json.loads((ROOT / "site.json").read_text())["indexnow_key"]
    assert (out / f"{key}.txt").read_text().strip() == key


def test_repo_with_own_pages_site_is_linked_not_generated(tmp_path):
    out = run(tmp_path)
    assert not (out / "dataset-x").exists()
    assert 'href="https://basitalisandhu.github.io/dataset-x/"' in (out / "index.html").read_text()


def test_repo_page_jsonld_and_escaping(tmp_path):
    html = (run(tmp_path) / "tool-one" / "index.html").read_text()
    (code,) = jsonld_blocks(html)
    assert code["@type"] == "SoftwareSourceCode"
    assert code["codeRepository"] == "https://github.com/basitalisandhu/tool-one"
    assert code["programmingLanguage"] == "Python"
    assert code["license"] == "https://spdx.org/licenses/MIT.html"
    assert code["author"]["sameAs"] == ["https://github.com/basitalisandhu"]
    assert code["version"] == "0.2.0"
    assert "things &amp; reports &lt;them&gt;" in html
    assert "<pre><code class=\"language-bash\">pipx install tool-one" in html
    assert "repo_name=tool-one" in html and "/tool-one/issues" in html


def test_home_has_person_and_themes(tmp_path):
    html = (run(tmp_path) / "index.html").read_text()
    blocks = jsonld_blocks(html)
    persons = [b for b in blocks if b["@type"] == "Person"]
    assert persons and persons[0]["sameAs"] == ["https://github.com/basitalisandhu"]
    assert '<h3 id="security-tooling">Security tooling</h3>' in html
    assert "v0.2.0" in html and "?tab=packages" in html
    assert '<a href="/posts/hello/">Hello</a>' in html
    assert '<link rel="canonical" href="https://basitalisandhu.github.io/">' in html


def test_post_has_blogposting(tmp_path):
    html = (run(tmp_path) / "posts" / "hello" / "index.html").read_text()
    (post,) = jsonld_blocks(html)
    assert post["@type"] == "BlogPosting" and post["datePublished"] == "2026-10-02"
    assert post["license"] == "https://creativecommons.org/licenses/by/4.0/"
    assert "print(&quot;&lt;b&gt;&quot;)" in html


def test_feed_sitemap_llms(tmp_path):
    out = run(tmp_path)
    feed = (out / "feed.xml").read_text()
    assert "<title>tool-one v0.2.0</title>" in feed and "<title>Hello</title>" in feed
    sitemap = (out / "sitemap.xml").read_text()
    assert "https://basitalisandhu.github.io/tool-one/</loc><lastmod>2026-10-04" in sitemap
    assert "dataset-x" not in sitemap
    llms = (out / "llms.txt").read_text()
    assert llms.startswith("# Muhammad Basit Ali\n\n> ")
    assert "- [tool-one](https://basitalisandhu.github.io/tool-one/): Tool one checks things." in llms
    assert "- [dataset-x](https://basitalisandhu.github.io/dataset-x/)" in llms


def test_fixture_site_passes_every_check(tmp_path):
    out = run(tmp_path)
    s = site.load_site(ROOT, FIX / "repos.json", FIX / "content")
    results = checks.run_all(out, s.url, s.cfg["indexnow_key"], {"https://basitalisandhu.github.io/dataset-x/"})
    assert results == {k: [] for k in results}


def test_build_is_deterministic(tmp_path):
    a, b = run(tmp_path / "a"), run(tmp_path / "b")
    files = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    assert files == sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    assert all((a / f).read_bytes() == (b / f).read_bytes() for f in files)


def test_refuses_to_clear_unmarked_directory(tmp_path):
    out = tmp_path / "docs"
    out.mkdir()
    (out / "precious.txt").write_text("x")
    try:
        build.main(["--out", str(out), "--data", str(FIX / "repos.json"), "--content", str(FIX / "content")])
    except SystemExit as e:
        assert "refusing" in str(e)
    else:
        raise AssertionError("expected SystemExit")
    assert (out / "precious.txt").exists()


def test_real_data_builds_and_passes_checks(tmp_path):
    out = tmp_path / "docs"
    assert build.main(["--out", str(out), "--check"]) == 0
