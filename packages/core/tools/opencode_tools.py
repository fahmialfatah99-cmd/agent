"""
OpenCode-Equivalent Tools Module
================================
Tools that mirror opencode's capabilities:
- File search (glob)
- Content search (grep)
- In-place file editing (search & replace)
- Web fetch
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from .registry import BaseTool, ToolResult, registry
from .linux_system import LinuxSystemTools


class GlobSearchTool(BaseTool):
    """Find files matching a glob pattern."""

    name = "file_search"
    description = "Find files matching a glob pattern (e.g. **/*.py, src/**/*.ts). Returns matching file paths."
    category = "filesystem"

    async def execute(self, pattern: str, path: str = ".") -> ToolResult:
        try:
            base = Path(path).expanduser().resolve()
            matched = [str(p) for p in base.glob(pattern)]
            if len(matched) > 200:
                truncated = matched[:200]
                result = {
                    "count": len(matched),
                    "truncated": True,
                    "matches": truncated,
                }
            else:
                result = {"count": len(matched), "matches": matched}
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GrepSearchTool(BaseTool):
    """Search file contents for a regex pattern."""

    name = "content_search"
    description = (
        "Search file contents for a regex pattern. Returns file paths and matching lines. "
        "Useful for finding where functions/variables are defined or referenced."
    )
    category = "filesystem"

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        include: Optional[str] = None,
        max_results: int = 50,
    ) -> ToolResult:
        try:
            base = Path(path).expanduser().resolve()
            if base.is_file():
                files = [base]
            else:
                files = list(base.rglob("*"))

            regex = re.compile(pattern)
            results = []
            total_matches = 0

            for file in files:
                if file.is_dir():
                    continue
                if include:
                    inc_pattern = re.compile(include.replace("*", ".*"))
                    if not inc_pattern.search(str(file)):
                        continue
                # Skip binary-ish files
                try:
                    if len(file.read_bytes()) > 2_000_000:
                        continue
                    text = file.read_text(encoding="utf-8", errors="ignore")
                except (PermissionError, OSError):
                    continue

                for line_no, line in enumerate(text.splitlines(), 1):
                    if regex.search(line):
                        results.append({
                            "file": str(file),
                            "line": line_no,
                            "content": line.strip()[:200],
                        })
                        total_matches += 1
                        if total_matches >= max_results:
                            return ToolResult(success=True, output={
                                "count": total_matches,
                                "truncated": True,
                                "matches": results,
                            })

            return ToolResult(success=True, output={
                "count": total_matches,
                "matches": results,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditFileTool(BaseTool):
    """In-place search-and-replace edit on a file."""

    name = "file_edit"
    description = (
        "Edit a file by replacing old_text with new_text. "
        "Controlled, does NOT overwrite whole file. Only the first occurrence is replaced."
    )
    category = "filesystem"

    async def execute(
        self,
        path: str,
        old_text: str,
        new_text: str,
    ) -> ToolResult:
        try:
            file_path = Path(path).expanduser().resolve()
            content = file_path.read_text(encoding="utf-8")
            count = content.count(old_text)
            if count == 0:
                return ToolResult(
                    success=False,
                    error=f"old_text not found in {file_path}",
                )
            new_content = content.replace(old_text, new_text, 1)
            file_path.write_text(new_content, encoding="utf-8")
            return ToolResult(success=True, output={
                "path": str(file_path),
                "replacements": 1,
                "total_occurrences": count,
            })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebFetchTool(BaseTool):
    """Fetch a URL and return its text content."""

    name = "web_fetch"
    description = (
        "Fetch a URL and return its content as text/markdown. "
        "Useful for reading web pages, documentation, or REST APIs."
    )
    category = "web"

    async def execute(self, url: str, timeout: float = 20.0) -> ToolResult:
        import httpx
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout),
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SuperAgent/1.0)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                content_type = resp.headers.get("content-type", "")
                if "text" in content_type or "json" in content_type or "xml" in content_type:
                    text = resp.text
                else:
                    return ToolResult(success=True, output={
                        "url": url,
                        "status": resp.status_code,
                        "content_type": content_type,
                        "note": "Binary response; content not shown",
                        "size": len(resp.content),
                    })

                # Strip common markup for compactness
                text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
                text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()

                return ToolResult(success=True, output={
                    "url": url,
                    "status": resp.status_code,
                    "content_type": content_type,
                    "content": text[:12000],
                })
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def register_opencode_tools() -> int:
    """Register all opencode-equivalent tools into the global registry."""
    tools = [
        GlobSearchTool(),
        GrepSearchTool(),
        EditFileTool(),
        WebFetchTool(),
    ]
    for tool_instance in tools:
        registry.register(tool_instance)
    return len(tools)


registered_count = register_opencode_tools()

__all__ = [
    "GlobSearchTool",
    "GrepSearchTool",
    "EditFileTool",
    "WebFetchTool",
    "register_opencode_tools",
]