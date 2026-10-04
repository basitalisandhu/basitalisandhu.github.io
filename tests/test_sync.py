import sync_repos as s

README = """# tool: a tool

[![CI](https://x/badge.svg)](https://x)
<p align="center">x</p>

Tool does a thing \u2014 quickly. See [docs](docs/a.md) and [usage](#usage).

![demo](docs/demo.svg)

## Install

```ini
@scope:registry=https://npm.pkg.github.com
```

```bash
pipx install tool   # see "Install" below
```

## Usage

text
"""

PROFILE = """# Name

## Skill packs

| Repository | What it is |
|---|---|
| [a-skills](https://github.com/o/a-skills) | Skills \u2014 for A. |

## Tools

| Repository | What it is |
|---|---|
| [t1](https://github.com/o/t1) | Tool one. |

### Latest releases

| Project | Latest release | Published |
|---|---|---|
| [t1](https://github.com/o/t1) | v1 | 2026 |
"""


def test_intro_strips_badges_html_images_and_absolutises_links():
    intro = s.readme_intro(README, "https://github.com/o/tool", "main")
    assert intro == ("Tool does a thing, quickly. See [docs](https://github.com/o/tool/blob/main/docs/a.md) "
                     "and [usage](https://github.com/o/tool#usage).")


def test_install_prefers_shell_and_drops_internal_pointer():
    assert s.readme_install(README) == {"lang": "bash", "code": "pipx install tool", "from": "Install"}
    assert s.readme_install("# x\n\n## Install\n\n```json\n{}\n```\n") is None


def test_profile_themes_and_one_liners():
    themes, one = s.profile_themes(PROFILE, "o")
    assert themes == [{"title": "Skill packs", "repos": ["a-skills"]}, {"title": "Tools", "repos": ["t1"]}]
    assert one == {"a-skills": "Skills, for A.", "t1": "Tool one."}


def test_short_line_and_fallback_theme():
    assert s.short_line("CI gate for Claude Code skills: scans things") == "CI gate for Claude Code skills."
    assert s.short_line("Short: x") == "Short: x"
    assert s.fallback_theme({"name": "mcp-x", "topics": []}) == "MCP tooling"
    assert s.fallback_theme({"name": "x-skills", "topics": ["agent-skills"]}) == "Claude Code skill packs"
    assert s.fallback_theme({"name": "data", "topics": ["dataset"]}) == "Data and lists"
    assert s.fallback_theme({"name": "gate", "topics": []}) == "Security tooling"


def test_changed_urls_mapping():
    import changed_urls as c

    site = "https://h.example"
    assert c.to_url(site, "docs/index.html") == "https://h.example/"
    assert c.to_url(site, "docs/tool/index.html") == "https://h.example/tool/"
    assert c.to_url(site, "docs/posts/a/index.html") == "https://h.example/posts/a/"
    assert c.to_url(site, "docs/404.html") is None
    assert c.to_url(site, "docs/feed.xml") is None
