"""
Advanced Linux Agent Integration Module.
Wraps LinuxSystemTools into proper tool classes for agent registry.
"""

from typing import Dict, Any, Optional, List
from .registry import BaseTool, ToolResult, tool, registry
from .linux_system import LinuxSystemTools


class ShellExecuteTool(BaseTool):
    """Execute arbitrary shell commands on Linux."""
    
    name = "linux_shell_execute"
    description = "Execute any shell command on the Linux system with full environment access"
    category = "system"
    
    async def execute(self, command: str, timeout: int = 60, cwd: Optional[str] = None) -> ToolResult:
        """
        Execute a shell command.
        
        Args:
            command: The shell command to execute
            timeout: Maximum execution time in seconds (default: 60)
            cwd: Working directory for the command
        
        Returns:
            ToolResult with stdout, stderr, and return code
        """
        result = LinuxSystemTools.execute_shell_command(command, timeout, cwd)
        
        return ToolResult(
            success=result.success,
            output={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.return_code,
                "command": result.command
            },
            metadata={"timeout": timeout, "cwd": cwd}
        )


class FileReadTool(BaseTool):
    """Read any file accessible by the current user."""
    
    name = "linux_file_read"
    description = "Read content from any file on the Linux filesystem"
    category = "filesystem"
    
    async def execute(self, path: str, binary: bool = False) -> ToolResult:
        """
        Read a file.
        
        Args:
            path: Path to the file
            binary: If True, read as binary (returns hex string)
        
        Returns:
            ToolResult with file content
        """
        result = LinuxSystemTools.read_file(path, binary)
        
        if result["success"]:
            return ToolResult(
                success=True,
                output=result["content"],
                metadata={"path": result["path"], "size": result["size"], "is_binary": result["is_binary"]}
            )
        else:
            return ToolResult(
                success=False,
                error=result.get("error", "Unknown error")
            )


class FileWriteTool(BaseTool):
    """Write content to any file where user has permissions."""
    
    name = "linux_file_write"
    description = "Write content to any file on the Linux filesystem"
    category = "filesystem"
    
    async def execute(
        self, 
        path: str, 
        content: str, 
        binary: bool = False, 
        append: bool = False
    ) -> ToolResult:
        """
        Write to a file.
        
        Args:
            path: Path to the file
            content: Content to write
            binary: If True, treat content as binary (hex string)
            append: If True, append to existing file
        
        Returns:
            ToolResult with operation status
        """
        result = LinuxSystemTools.write_file(path, content, binary, append)
        
        if result["success"]:
            return ToolResult(
                success=True,
                output=f"Successfully wrote {result['bytes_written']} bytes",
                metadata={"path": result["path"], "bytes_written": result["bytes_written"]}
            )
        else:
            return ToolResult(
                success=False,
                error=result.get("error", "Unknown error")
            )


class DirectoryListTool(BaseTool):
    """List directory contents with metadata."""
    
    name = "linux_directory_list"
    description = "List contents of a directory with detailed metadata"
    category = "filesystem"
    
    async def execute(self, path: str, recursive: bool = False) -> ToolResult:
        """
        List directory contents.
        
        Args:
            path: Path to the directory
            recursive: If True, list recursively
        
        Returns:
            ToolResult with directory listing
        """
        result = LinuxSystemTools.list_directory(path, recursive)
        
        if result["success"]:
            return ToolResult(
                success=True,
                output=result["contents"],
                metadata={"count": result["count"], "recursive": recursive}
            )
        else:
            return ToolResult(
                success=False,
                error=result.get("error", "Unknown error")
            )


class ProcessManagerTool(BaseTool):
    """Manage system processes."""
    
    name = "linux_process_manager"
    description = "Manage system processes (kill, terminate, pause, resume, info)"
    category = "system"
    
    async def execute(self, action: str, identifier: Any) -> ToolResult:
        """
        Manage a process.
        
        Args:
            action: One of 'kill', 'terminate', 'pause', 'resume', 'info'
            identifier: PID (int) or process name (str)
        
        Returns:
            ToolResult with process information
        """
        # Convert identifier to appropriate type
        try:
            pid = int(identifier)
            processed_id = pid
        except (ValueError, TypeError):
            processed_id = str(identifier)
        
        result = LinuxSystemTools.manage_process(action, processed_id)
        
        if result["success"]:
            return ToolResult(
                success=True,
                output=result["results"],
                metadata={"action": action, "identifier": processed_id}
            )
        else:
            return ToolResult(
                success=False,
                error=result.get("error", "Unknown error")
            )


class SystemInfoTool(BaseTool):
    """Get comprehensive system information."""
    
    name = "linux_system_info"
    description = "Retrieve comprehensive system information including memory, CPU, and platform details"
    category = "system"
    
    async def execute(self) -> ToolResult:
        """
        Get system information.
        
        Returns:
            ToolResult with system details
        """
        info = LinuxSystemTools.get_system_info()
        
        return ToolResult(
            success=True,
            output=info,
            metadata={"retrieved_at": "now"}
        )


class NetworkScanTool(BaseTool):
    """Scan TCP ports on a host."""
    
    name = "linux_network_scan"
    description = "Scan TCP ports on a specified host"
    category = "network"
    
    async def execute(self, host: str, ports: List[int], timeout: float = 1.0) -> ToolResult:
        """
        Scan ports on a host.
        
        Args:
            host: Hostname or IP address
            ports: List of port numbers to scan
            timeout: Connection timeout in seconds
        
        Returns:
            ToolResult with open ports
        """
        result = LinuxSystemTools.network_scan(host, ports, timeout)
        
        if result["success"]:
            return ToolResult(
                success=True,
                output=result["open_ports"],
                metadata={"host": result["host"], "scanned_ports": len(ports)}
            )
        else:
            return ToolResult(
                success=False,
                error=result.get("error", "Unknown error")
            )


# Auto-register all tools when module is imported
def register_linux_tools():
    """Register all Linux system tools to the global registry."""
    tools = [
        ShellExecuteTool(),
        FileReadTool(),
        FileWriteTool(),
        DirectoryListTool(),
        ProcessManagerTool(),
        SystemInfoTool(),
        NetworkScanTool(),
    ]
    
    for tool_instance in tools:
        registry.register(tool_instance)
    
    return len(tools)


# Auto-register on import
registered_count = register_linux_tools()
print(f"[LinuxAgent] Registered {registered_count} advanced Linux tools")

__all__ = [
    "ShellExecuteTool",
    "FileReadTool",
    "FileWriteTool",
    "DirectoryListTool",
    "ProcessManagerTool",
    "SystemInfoTool",
    "NetworkScanTool",
    "register_linux_tools",
]
