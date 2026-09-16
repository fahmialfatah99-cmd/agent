"""
Advanced Linux System Tools Module.
Provides unrestricted access to Linux system capabilities within the user's permission scope.
Includes shell execution, file system manipulation, process management, and network tools.
"""

import os
import sys
import stat
import signal
import asyncio
import subprocess
import shutil
import socket
import psutil
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Iterator, Tuple
from dataclasses import dataclass

@dataclass
class CommandResult:
    """Standardized output for system commands."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    command: str

class LinuxSystemTools:
    """
    High-privilege toolset for Linux system interaction.
    WARNING: Use with caution. Executes commands with the current user's permissions.
    """

    # Directories that are rarely relevant for "find junk" scans and can be huge.
    HEAVY_SCAN_DIRS: frozenset = frozenset({
        "node_modules", ".git", ".svn", ".hg", ".venv", "venv", "env",
        "__pycache__", ".cache", ".next", ".nuxt", ".turbo", ".tox",
        ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
        "target", ".gradle", ".angular", "coverage",
    })

    @staticmethod
    def walk_paths(
        path: str,
        timeout: float = 20.0,
        max_items: int = 20000,
        skip_heavy: bool = True,
    ) -> Iterator[Tuple[Optional[str], bool]]:
        """
        Walk a directory tree with a hard time budget and item cap.

        Yields (entry_path, is_dir) tuples. When the walk stops early because
        the budget was exhausted, it yields (None, reason) once, where reason
        is "timeout" or "max_items".
        """
        import time as time_mod

        deadline = time_mod.monotonic() + timeout if timeout and timeout > 0 else 0
        limit = max_items if max_items and max_items > 0 else 20000

        start = Path(path).expanduser().resolve()
        stack = [start]
        seen = 0

        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if seen >= limit:
                            yield None, "max_items"
                            return
                        if deadline and time_mod.monotonic() > deadline:
                            yield None, "timeout"
                            return

                        seen += 1
                        try:
                            st = entry.stat(follow_symlinks=False)
                        except (PermissionError, OSError):
                            yield entry.path, False
                            continue

                        is_dir = stat.S_ISDIR(st.st_mode)
                        if is_dir and skip_heavy and entry.name in LinuxSystemTools.HEAVY_SCAN_DIRS:
                            continue
                        if is_dir:
                            stack.append(entry.path)
                        yield entry.path, is_dir
            except (PermissionError, OSError):
                continue

    @staticmethod
    def execute_shell_command(command: str, timeout: int = 60, cwd: Optional[str] = None) -> CommandResult:
        """
        Execute any shell command with full environment access.
        
        Args:
            command: The shell command to execute.
            timeout: Maximum execution time in seconds.
            cwd: Working directory for the command.
        
        Returns:
            CommandResult object containing output and status.
        """
        try:
            # Using shell=True for full shell features (pipes, redirects, etc.)
            # Security Note: Ensure 'command' is validated if derived from untrusted input.
            # Here we assume the agent logic validates the intent.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=os.environ  # Inherit full environment
            )
            return CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                command=command
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1,
                command=command
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command
            )

    @staticmethod
    async def aexecute_shell_command(command: str, timeout: int = 30, cwd: Optional[str] = None) -> CommandResult:
        """
        Execute a shell command asynchronously.

        Unlike execute_shell_command (which blocks a thread and cannot be
        interrupted), this runs in the event loop and the subprocess is killed
        when the timeout fires, so timeouts return fast and leave no stray
        processes scanning the disk.
        """
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=os.environ,
                start_new_session=True,
            )
            try:
                stdout_b, stderr_b = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                # Kill the whole process group so grandchildren (e.g. `sleep 30`,
                # `du /`) don't keep the pipes open and stall the timeout.
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    try:
                        proc.kill()
                    except ProcessLookupError:
                        pass
                stdout_b, stderr_b = await proc.communicate()
                return CommandResult(
                    success=False,
                    stdout=stdout_b.decode(errors="replace"),
                    stderr=f"Command timed out after {timeout} seconds\n{stderr_b.decode(errors='replace')}",
                    return_code=-1,
                    command=command
                )

            return CommandResult(
                success=proc.returncode == 0,
                stdout=stdout_b.decode(errors="replace"),
                stderr=stderr_b.decode(errors="replace"),
                return_code=proc.returncode,
                command=command
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                command=command
            )

    @staticmethod
    def read_file(path: str, binary: bool = False) -> Dict[str, Any]:
        """Read any file accessible by the current user."""
        try:
            file_path = Path(path).expanduser().resolve()
            if not file_path.exists():
                return {"success": False, "error": "File not found", "content": None}
            
            mode = 'rb' if binary else 'r'
            content = file_path.read_bytes() if binary else file_path.read_text(encoding='utf-8', errors='ignore')
            
            return {
                "success": True,
                "path": str(file_path),
                "size": len(content),
                "content": content if not binary else content.hex(),
                "is_binary": binary
            }
        except PermissionError:
            return {"success": False, "error": "Permission denied", "content": None}
        except Exception as e:
            return {"success": False, "error": str(e), "content": None}

    @staticmethod
    def write_file(path: str, content: str, binary: bool = False, append: bool = False) -> Dict[str, Any]:
        """Write content to any file where the user has write permissions."""
        try:
            file_path = Path(path).expanduser().resolve()
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'ab' if append and binary else ('a' if append else 'wb' if binary else 'w')
            data = content.encode() if binary else content
            
            with open(file_path, mode) as f:
                f.write(data)
            
            return {"success": True, "path": str(file_path), "bytes_written": len(data)}
        except PermissionError:
            return {"success": False, "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_directory(
        path: str,
        recursive: bool = False,
        timeout: float = 30.0,
        max_items: int = 20000,
        skip_heavy: bool = True,
    ) -> Dict[str, Any]:
        """List directory contents with detailed metadata."""
        try:
            dir_path = Path(path).expanduser().resolve()
            if not dir_path.is_dir():
                return {"success": False, "error": "Not a directory"}

            # Hard safety caps: regardless of what the caller/LLM passes, a
            # recursive listing can never run away for minutes.
            timeout = min(float(timeout or 0) if timeout else 30.0, 30.0)
            max_items = min(int(max_items) if max_items else 20000, 20000)

            files = []
            stop_reason = None

            if recursive:
                for item_path, is_dir in LinuxSystemTools.walk_paths(
                    str(dir_path), timeout=timeout, max_items=max_items, skip_heavy=skip_heavy
                ):
                    if item_path is None:
                        stop_reason = is_dir  # "timeout" or "max_items"
                        break
                    try:
                        p = Path(item_path)
                        st = p.stat()
                        files.append({
                            "name": p.name,
                            "path": str(p),
                            "type": "directory" if is_dir else "file",
                            "size": st.st_size,
                            "permissions": oct(st.st_mode)[-3:]
                        })
                    except PermissionError:
                        files.append({"name": str(p), "path": str(p), "error": "Permission denied"})
                    except OSError:
                        pass
            else:
                iterator = dir_path.iterdir()
                if max_items and max_items > 0:
                    iterator = (e for i, e in enumerate(iterator) if i < max_items)
                for item in iterator:
                    try:
                        stat_res = item.stat()
                        files.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory" if item.is_dir() else "file",
                            "size": stat_res.st_size,
                            "permissions": oct(stat_res.st_mode)[-3:]
                        })
                    except PermissionError:
                        files.append({"name": item.name, "path": str(item), "error": "Permission denied"})
                    except OSError:
                        pass

            result: Dict[str, Any] = {
                "success": True,
                "count": len(files),
                "contents": files,
                "truncated": stop_reason is not None,
                "truncated_reason": stop_reason,
            }
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def manage_process(action: str, identifier: Union[int, str]) -> Dict[str, Any]:
        """
        Manage system processes (kill, pause, resume, info).
        Identifier can be PID (int) or process name (str).
        """
        try:
            procs = []
            if isinstance(identifier, int):
                procs = [psutil.Process(identifier)]
            else:
                # Find by name
                procs = [p for p in psutil.process_iter(['pid', 'name']) if p.info['name'] == identifier]
            
            results = []
            for p in procs:
                try:
                    info = {"pid": p.pid, "name": p.name(), "status": p.status()}
                    
                    if action == "kill":
                        p.kill()
                        info["action_result"] = "killed"
                    elif action == "terminate":
                        p.terminate()
                        info["action_result"] = "terminated"
                    elif action == "pause":
                        p.suspend()
                        info["action_result"] = "paused"
                    elif action == "resume":
                        p.resume()
                        info["action_result"] = "resumed"
                    elif action == "info":
                        info["action_result"] = "info_retrieved"
                        info["cpu_percent"] = p.cpu_percent()
                        info["memory_percent"] = p.memory_percent()
                        info["cmdline"] = p.cmdline()
                    
                    results.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    results.append({"identifier": identifier, "error": str(e)})
            
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Retrieve comprehensive system information."""
        return {
            "platform": sys.platform,
            "python_version": sys.version,
            "cwd": os.getcwd(),
            "user": os.getenv("USER"),
            "home": os.getenv("HOME"),
            "cpu_count": os.cpu_count(),
            "boot_time": psutil.boot_time(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk_usage": {
                "/": shutil.disk_usage("/") if os.path.exists("/") else None
            }
        }

    @staticmethod
    def network_scan(host: str, ports: List[int], timeout: float = 1.0) -> Dict[str, Any]:
        """Simple TCP port scanner."""
        open_ports = []
        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            
            return {"success": True, "host": host, "open_ports": open_ports}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Export for easy importing
__all__ = ["LinuxSystemTools", "CommandResult"]
