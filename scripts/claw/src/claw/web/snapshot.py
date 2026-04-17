"""claw web snapshot — inline page assets as data URIs (monolith-style)."""

from __future__ import annotations

import base64
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import click

from claw.common import (
    EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, safe_write,
)


DEFAULT_UA = "claw/1.0 (+https://github.com/anthropic/claude-claw)"


def _guess_mime(url: str, default: str = "application/octet-stream") -> str:
    mime, _ = mimetypes.guess_type(urlparse(url).path)
    return mime or default


def _to_data_uri(content: bytes, mime: str) -> str:
    b64 = base64.b64encode(content).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _same_origin(url: str, base: str) -> bool:
    u, b = urlparse(url), urlparse(base)
    return (u.scheme, u.netloc) == (b.scheme, b.netloc)


_CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")


def _inline_css_urls(css: str, base_url: str, fetcher, strict: bool) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(1).strip()
        if raw.startswith("data:"):
            return m.group(0)
        absolute = urljoin(base_url, raw)
        if strict and not _same_origin(absolute, base_url):
            sys.stderr.write(f"warning: skipping cross-origin css asset {absolute}\n")
            return m.group(0)
        try:
            data = fetcher(absolute)
            if data is None:
                return m.group(0)
            mime = _guess_mime(absolute)
            return f"url({_to_data_uri(data, mime)})"
        except Exception as e:
            sys.stderr.write(f"warning: failed to inline {absolute}: {e}\n")
            return m.group(0)

    return _CSS_URL_RE.sub(repl, css)


@click.command(name="snapshot")
@click.argument("url")
@click.option("--out", required=True, type=click.Path(path_type=Path))
@click.option("--strict", is_flag=True,
              help="Skip cross-origin assets with a stderr warning.")
@click.option("--timeout", default=30.0, type=float)
@click.option("--ua", default=DEFAULT_UA)
@click.option("--as", "as_fmt",
              type=click.Choice(["html", "mhtml", "markdown", "pdf"]),
              default="html",
              help="Snapshot output format (default html). "
                   "TODO: only html is implemented in-process; the other formats "
                   "currently fall back to single-file html.")
@common_output_options
def snapshot(url: str, out: Path, strict: bool, timeout: float, ua: str,
             as_fmt: str,
             force: bool, backup: bool, as_json: bool, dry_run: bool,
             quiet: bool, verbose: bool, mkdir: bool) -> None:
    """Fetch a page and inline every stylesheet/image/font as data: URIs."""
    try:
        import httpx
    except ImportError:
        die("httpx not installed", code=EXIT_INPUT,
            hint="pip install 'claw[web]'", as_json=as_json)
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        die("beautifulsoup4 not installed", code=EXIT_INPUT,
            hint="pip install 'claw[html]'", as_json=as_json)

    if dry_run:
        click.echo(f"would snapshot {url} → {out}")
        return

    headers = {"User-Agent": ua}
    client = httpx.Client(follow_redirects=True, timeout=timeout, headers=headers)

    fetch_cache: dict[str, bytes | None] = {}

    def fetch(u: str) -> bytes | None:
        if u in fetch_cache:
            return fetch_cache[u]
        try:
            resp = client.get(u)
            resp.raise_for_status()
            fetch_cache[u] = resp.content
            return resp.content
        except Exception as e:
            sys.stderr.write(f"warning: fetch failed {u}: {e}\n")
            fetch_cache[u] = None
            return None

    try:
        page = client.get(url)
        page.raise_for_status()
    except httpx.HTTPError as e:
        client.close()
        die(f"fetch failed: {e}", code=EXIT_SYSTEM, as_json=as_json)
        return

    base_url = str(page.url)
    soup = BeautifulSoup(page.text, "lxml")

    inlined = {"css": 0, "img": 0, "font": 0, "script": 0, "skipped": 0}

    for link in soup.find_all("link", rel=True):
        rels = [r.lower() for r in (link.get("rel") or [])]
        if "stylesheet" not in rels:
            continue
        href = link.get("href")
        if not href:
            continue
        absolute = urljoin(base_url, href)
        if strict and not _same_origin(absolute, base_url):
            sys.stderr.write(f"warning: skipping cross-origin stylesheet {absolute}\n")
            inlined["skipped"] += 1
            continue
        data = fetch(absolute)
        if data is None:
            inlined["skipped"] += 1
            continue
        css_text = data.decode("utf-8", errors="replace")
        css_text = _inline_css_urls(css_text, absolute, fetch, strict)
        style_tag = soup.new_tag("style")
        style_tag.string = css_text
        link.replace_with(style_tag)
        inlined["css"] += 1

    for style in soup.find_all("style"):
        if style.string:
            style.string = _inline_css_urls(style.string, base_url, fetch, strict)

    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src.startswith("data:"):
            continue
        absolute = urljoin(base_url, src)
        if strict and not _same_origin(absolute, base_url):
            sys.stderr.write(f"warning: skipping cross-origin image {absolute}\n")
            inlined["skipped"] += 1
            continue
        data = fetch(absolute)
        if data is None:
            inlined["skipped"] += 1
            continue
        img["src"] = _to_data_uri(data, _guess_mime(absolute, "image/png"))
        if img.has_attr("srcset"):
            del img["srcset"]
        inlined["img"] += 1

    for script in soup.find_all("script", src=True):
        src = script.get("src")
        absolute = urljoin(base_url, src)
        if strict and not _same_origin(absolute, base_url):
            sys.stderr.write(f"warning: skipping cross-origin script {absolute}\n")
            inlined["skipped"] += 1
            continue
        data = fetch(absolute)
        if data is None:
            inlined["skipped"] += 1
            continue
        del script["src"]
        script.string = data.decode("utf-8", errors="replace")
        inlined["script"] += 1

    client.close()

    result = str(soup).encode("utf-8")
    safe_write(out, lambda f: f.write(result),
               force=force, backup=backup, mkdir=mkdir)

    if as_json:
        emit_json({"url": url, "out": str(out), "bytes": len(result),
                   "as": as_fmt, **inlined})
    elif not quiet:
        click.echo(f"snapshot {url} → {out} "
                   f"(css={inlined['css']} img={inlined['img']} "
                   f"script={inlined['script']} skipped={inlined['skipped']})",
                   err=True)
