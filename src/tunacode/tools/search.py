import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Generator, List

from tinyagent.decorators import tool

CHUNK = 100  # lines / paths per yield
DEFAULT_MAX = 500  # sane cap for token budget


def _yield_chunks(items, chunk=CHUNK):
    buf = []
    for it in items:
        buf.append(it)
        if len(buf) >= chunk:
            yield buf
            buf = []
    if buf:
        yield buf


@tool(read_only=True, name="ls_tree")
def ls_tree(
    dir: str = ".", max_paths: int = DEFAULT_MAX, max_depth: int = 3, include_hidden: bool = False
) -> Generator[List[str], None, None]:
    """List up to `max_paths` relative paths under `dir`, breadth-first."""
    root = Path(dir).resolve()
    count = 0
    for path in root.rglob("*"):
        if not include_hidden and any(p.startswith(".") for p in path.parts):
            continue
        depth = len(path.relative_to(root).parts)
        if depth > max_depth:
            continue
        yield from _yield_chunks([str(path.relative_to(root))])
        count += 1
        if count >= max_paths:
            break


@tool(read_only=True, name="glob_find")
def glob_find(
    pattern: str, dir: str = ".", max_matches: int = DEFAULT_MAX
) -> Generator[List[str], None, None]:
    """Return paths matching a glob pattern (e.g. **/*.py)."""
    root = Path(dir).resolve()
    matches = root.glob(pattern)
    yielded = 0
    for chunk in _yield_chunks(str(p) for p in matches):
        yield chunk
        yielded += len(chunk)
        if yielded >= max_matches:
            break


@tool(read_only=True, name="grep_rg")
def grep_rg(
    pattern: str,
    dir: str = ".",
    ignore_case: bool = False,
    max_hits: int = DEFAULT_MAX,
    context: int = 0,
) -> Generator[List[Dict], None, None]:
    """Regex search using ripgrep or Python fallback."""
    root = Path(dir).resolve()
    args = ["rg", "-n", "--json", "-C", str(context), pattern, str(root)]
    if ignore_case:
        args.insert(1, "-i")

    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, text=True, bufsize=1)
        hits = 0
        buf = []
        for line in proc.stdout:
            evt = json.loads(line)
            if evt.get("type") != "match":
                continue
            mat = evt["data"]
            buf.append(
                {
                    "file": mat["path"]["text"],
                    "line": mat["lines"]["line_number"],
                    "text": mat["lines"]["text"].rstrip(),
                }
            )
            if len(buf) >= CHUNK:
                yield buf
                buf = []
            hits += 1
            if hits >= max_hits:
                proc.kill()
                break
        if buf:
            yield buf
    except FileNotFoundError:
        rx = re.compile(pattern, re.I if ignore_case else 0)
        hits = 0
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            for i, ln in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                if rx.search(ln):
                    yield [{"file": str(p), "line": i, "text": ln.strip()}]
                    hits += 1
                    if hits >= max_hits:
                        return
