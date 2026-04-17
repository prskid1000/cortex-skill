"""Shared HTTP helpers for `claw web`: proxy parsing + retry envelope.

Kept separate so both `fetch` and `extract` share the same semantics for
`--proxy`, `--retry-on`, `--retries`, `--timeout`. httpx is imported lazily
inside the helpers so importing this module has no runtime dep cost.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Iterable

import click


RETRY_CONDITIONS = {"4xx", "5xx", "429", "503", "timeout", "connection"}
DEFAULT_RETRY_ON = "5xx,429,timeout,connection"


def parse_retry_on(value: str | None) -> set[str]:
    if not value:
        return set()
    out: set[str] = set()
    for tok in value.split(","):
        t = tok.strip().lower()
        if not t:
            continue
        if t not in RETRY_CONDITIONS:
            raise click.BadParameter(
                f"--retry-on {t!r} not in {{{', '.join(sorted(RETRY_CONDITIONS))}}}"
            )
        out.add(t)
    return out


def parse_proxies(items: Iterable[str]) -> str | dict[str, str] | None:
    """Return either None, a single URL (both schemes), or a {scheme://: url} map.

    Accepts:
      --proxy http://p            single URL, applies to http+https
      --proxy http=http://p       scheme-scoped
      --proxy http=http://p --proxy https=http://q    multi-scheme
    """
    items = [x for x in items if x]
    if not items:
        return None
    if len(items) == 1 and "=" not in items[0].split("://", 1)[0]:
        # URL form: "=" only after scheme, which means no scheme prefix. Heuristic:
        # treat single bare URL as "applies to both".
        tok = items[0]
        if not _looks_scheme_scoped(tok):
            return tok
    mapping: dict[str, str] = {}
    for it in items:
        if not _looks_scheme_scoped(it):
            raise click.BadParameter(
                f"--proxy {it!r}: use SCHEME=URL when passing multiple "
                f"(e.g. http=http://p1 https=http://p2)"
            )
        scheme, url = it.split("=", 1)
        scheme = scheme.strip().lower()
        if scheme not in {"http", "https", "all"}:
            raise click.BadParameter(
                f"--proxy scheme {scheme!r}: expected http, https, or all"
            )
        if scheme == "all":
            mapping["http://"] = url
            mapping["https://"] = url
        else:
            mapping[f"{scheme}://"] = url
    return mapping


def _looks_scheme_scoped(token: str) -> bool:
    """True when token matches `scheme=URL` form (and not `http://host`)."""
    if "=" not in token:
        return False
    head = token.split("=", 1)[0].strip().lower()
    return head in {"http", "https", "all"}


def build_client(httpx_module: Any, *, timeout: float, follow_redirects: bool = True,
                 max_redirects: int = 20, proxy: str | dict[str, str] | None = None,
                 cookies: Any = None, headers: dict[str, str] | None = None) -> Any:
    kwargs: dict[str, Any] = {
        "follow_redirects": follow_redirects,
        "max_redirects": max_redirects,
        "timeout": timeout,
        "cookies": cookies,
    }
    if headers:
        kwargs["headers"] = headers
    if isinstance(proxy, dict):
        mounts = {}
        for scheme_prefix, url in proxy.items():
            mounts[scheme_prefix] = httpx_module.HTTPTransport(proxy=url)
        kwargs["mounts"] = mounts
    elif isinstance(proxy, str):
        kwargs["proxy"] = proxy
    return httpx_module.Client(**kwargs)


def _classify_exception(httpx_module: Any, exc: BaseException) -> str | None:
    """Map an httpx exception to a retry condition token, or None if unclassified."""
    if isinstance(exc, httpx_module.TimeoutException):
        return "timeout"
    # Connection-ish failures — covers ConnectError, ReadError, RemoteProtocolError, etc.
    if isinstance(exc, (httpx_module.ConnectError, httpx_module.NetworkError,
                        httpx_module.RemoteProtocolError, httpx_module.ReadError,
                        httpx_module.WriteError, httpx_module.CloseError)):
        return "connection"
    return None


def should_retry_status(status: int, retry_on: set[str]) -> bool:
    if status == 429 and "429" in retry_on:
        return True
    if status == 503 and ("503" in retry_on or "5xx" in retry_on):
        return True
    if 500 <= status < 600 and "5xx" in retry_on:
        return True
    if 400 <= status < 500 and "4xx" in retry_on:
        return True
    return False


def _backoff(attempt: int) -> float:
    # 0.5, 1, 2, 4, 8, 8, 8...
    return min(0.5 * (2 ** attempt), 8.0)


def request_with_retries(client: Any, httpx_module: Any, *, method: str, url: str,
                         headers: dict[str, str] | None = None,
                         content: bytes | None = None,
                         retries: int = 0, retry_on: set[str] | None = None,
                         sleep: Callable[[float], None] = time.sleep) -> Any:
    """Run client.request with exponential-backoff retry honoring `retry_on`.

    Returns a response. Re-raises the final httpx exception if all retries are
    exhausted on a network error.
    """
    retry_on = retry_on or set()
    attempt = 0
    while True:
        try:
            resp = client.request(method.upper(), url, headers=headers, content=content)
            if attempt < retries and should_retry_status(resp.status_code, retry_on):
                sleep(_backoff(attempt))
                attempt += 1
                continue
            return resp
        except httpx_module.HTTPError as e:
            cond = _classify_exception(httpx_module, e)
            if attempt < retries and cond and cond in retry_on:
                sleep(_backoff(attempt))
                attempt += 1
                continue
            raise


def fetch_bytes(httpx_module: Any, url: str, *, timeout: float,
                retries: int, retry_on: set[str],
                proxy: str | dict[str, str] | None,
                headers: dict[str, str] | None = None) -> tuple[int, bytes, str]:
    """One-shot helper used by `extract` URL-mode. Returns (status, body, final_url)."""
    client = build_client(
        httpx_module, timeout=timeout, follow_redirects=True,
        proxy=proxy, headers=headers,
    )
    try:
        resp = request_with_retries(
            client, httpx_module, method="GET", url=url,
            retries=retries, retry_on=retry_on,
        )
        return resp.status_code, resp.content, str(resp.url)
    finally:
        client.close()
