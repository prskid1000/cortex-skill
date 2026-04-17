"""claw web fetch — HTTP GET/POST with cookies, headers, retries."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import click

from claw.common import (
    EXIT_INPUT, EXIT_SYSTEM, common_output_options, die, emit_json, safe_write,
)
from claw.web._http import (
    DEFAULT_RETRY_ON, build_client, parse_proxies, parse_retry_on,
    request_with_retries,
)

DEFAULT_UA = "claw/1.0 (+https://github.com/anthropic/claude-claw)"


def _parse_kv_pair(items: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for it in items:
        if "=" not in it:
            raise click.BadParameter(f"expected K=V, got {it!r}")
        k, v = it.split("=", 1)
        out[k.strip()] = v
    return out


def _resolve_data(data: str | None) -> bytes | None:
    if data is None:
        return None
    if data.startswith("@"):
        return Path(data[1:]).read_bytes()
    return data.encode("utf-8")


def _post_process(body: bytes, precision: str | None, fmt: str | None,
                  selector: str | None, *, as_json: bool) -> bytes:
    """Scope by --selector, extract by --precision, render as --format."""
    html = body.decode("utf-8", errors="replace")

    if selector:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            die("beautifulsoup4 not installed (needed for --selector)",
                code=EXIT_INPUT, hint="pip install 'claw[html]'", as_json=as_json)
        soup = BeautifulSoup(html, "lxml")
        picked = soup.select(selector)
        html = "\n".join(str(el) for el in picked)

    if fmt is None and precision is None:
        return html.encode("utf-8")

    effective_fmt = fmt or "text"
    if effective_fmt == "html":
        return html.encode("utf-8")

    try:
        import trafilatura
    except ImportError:
        die("trafilatura not installed (needed for --precision/--format)",
            code=EXIT_INPUT, hint="pip install 'claw[web]'", as_json=as_json)

    output_format = {"text": "txt", "markdown": "markdown", "json": "json",
                     "html": "html"}[effective_fmt]
    kwargs: dict = {
        "output_format": output_format,
        "include_comments": False,
        "include_tables": True,
    }
    if precision == "thorough":
        kwargs["favor_recall"] = True
    elif precision == "fast":
        kwargs["favor_precision"] = True
    result = trafilatura.extract(html, **kwargs) or ""
    return result.encode("utf-8")


@click.command(name="fetch")
@click.argument("url")
@click.option("--out", default=None, type=click.Path(path_type=Path),
              help="Output file or `-` for stdout (default: stdout).")
@click.option("--method", default="GET",
              type=click.Choice(["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"],
                                case_sensitive=False))
@click.option("--header", "headers", multiple=True, metavar="K=V",
              help="Request header (repeatable).")
@click.option("--data", default=None, help="Request body. Prefix @ to load from file.")
@click.option("--timeout", default=30.0, type=float, help="Seconds (default 30).")
@click.option("--retries", default=0, type=int, help="Retries on matching --retry-on conditions.")
@click.option("--retry-on", "retry_on", default=DEFAULT_RETRY_ON,
              help=(f"Comma-separated conditions: 4xx,5xx,429,503,timeout,connection. "
                    f"Default: {DEFAULT_RETRY_ON}."))
@click.option("--follow-redirects/--no-follow-redirects", default=True)
@click.option("--max-redirects", default=20, type=int)
@click.option("--save-cookies", default=None, type=click.Path(path_type=Path))
@click.option("--load-cookies", default=None, type=click.Path(path_type=Path, exists=True))
@click.option("--ua", default=DEFAULT_UA, help="User-Agent string.")
@click.option("--proxy", "proxies", multiple=True, metavar="[SCHEME=]URL",
              help=("Proxy URL. Repeatable as SCHEME=URL for per-scheme proxies: "
                    "`--proxy http=http://p1 --proxy https=http://p2`. "
                    "A single URL form applies to both schemes."))
@click.option("--accept-errors", is_flag=True, help="Don't exit non-zero on HTTP >= 400.")
@click.option("--precision", "precision",
              type=click.Choice(["fast", "balanced", "thorough"]),
              default=None,
              help="Content-extraction precision preset applied to the fetched body. "
                   "Only takes effect together with --format or --selector.")
@click.option("--format", "fmt",
              type=click.Choice(["text", "html", "markdown", "json"]),
              default=None,
              help="Post-process the fetched body into this output format "
                   "(text|html|markdown|json).")
@click.option("--selector", "selector", default=None,
              help="CSS selector to scope extraction before --format is applied.")
# TODO: --precision/--format/--selector are doc-scoped to `web fetch` but the
# actual extraction verb is `web extract`. Implemented here as read-emit
# post-processing over the fetched body; leaves raw fetch behavior unchanged
# when none of the three are passed.
@common_output_options
def fetch(url: str, out: Path | None, method: str, headers: tuple[str, ...],
          data: str | None, timeout: float, retries: int, retry_on: str,
          follow_redirects: bool,
          max_redirects: int, save_cookies: Path | None, load_cookies: Path | None,
          ua: str, proxies: tuple[str, ...], accept_errors: bool,
          precision: str | None, fmt: str | None, selector: str | None,
          force: bool, backup: bool, as_json: bool, dry_run: bool,
          quiet: bool, verbose: bool, mkdir: bool) -> None:
    """HTTP GET/POST a URL; write body to --out or stdout."""
    try:
        import httpx
    except ImportError:
        die("httpx not installed", code=EXIT_INPUT,
            hint="pip install 'claw[web]'", as_json=as_json)

    try:
        hdrs = _parse_kv_pair(headers)
        retry_conditions = parse_retry_on(retry_on)
        proxy = parse_proxies(proxies)
    except click.BadParameter as e:
        die(str(e), code=EXIT_INPUT, as_json=as_json)
    hdrs.setdefault("User-Agent", ua)
    body = _resolve_data(data)

    cookies = None
    if load_cookies:
        from http.cookiejar import MozillaCookieJar
        jar = MozillaCookieJar(str(load_cookies))
        jar.load(ignore_discard=True, ignore_expires=True)
        cookies = jar

    if dry_run:
        if as_json:
            emit_json({"would_fetch": url, "method": method.upper(), "headers": hdrs})
        else:
            click.echo(f"would {method.upper()} {url}")
        return

    client = build_client(
        httpx, timeout=timeout, follow_redirects=follow_redirects,
        max_redirects=max_redirects, proxy=proxy, cookies=cookies,
    )
    start = time.monotonic()
    try:
        try:
            resp = request_with_retries(
                client, httpx, method=method, url=url, headers=hdrs, content=body,
                retries=retries, retry_on=retry_conditions,
            )
        except httpx.HTTPError as e:
            die(f"network error: {e}", code=EXIT_SYSTEM, as_json=as_json)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if save_cookies:
            from http.cookiejar import MozillaCookieJar
            jar = MozillaCookieJar(str(save_cookies))
            for c in client.cookies.jar:
                jar.set_cookie(c)
            jar.save(ignore_discard=True, ignore_expires=True)

        content = resp.content
        if precision or fmt or selector:
            content = _post_process(content, precision, fmt, selector, as_json=as_json)
        if out is None or str(out) == "-":
            sys.stdout.buffer.write(content)
            body_path = None
        else:
            safe_write(out, lambda f: f.write(content),
                       force=force, backup=backup, mkdir=mkdir)
            body_path = str(out)

        if as_json:
            emit_json({
                "url": url, "status": resp.status_code, "final_url": str(resp.url),
                "headers": dict(resp.headers), "body_path": body_path,
                "size": len(content), "elapsed_ms": elapsed_ms,
            })
        elif not quiet and body_path:
            click.echo(f"{resp.status_code} {resp.reason_phrase} -> {body_path} ({len(content)} bytes, {elapsed_ms}ms)",
                       err=True)

        if resp.status_code >= 400 and not accept_errors:
            sys.exit(6)
    finally:
        client.close()
