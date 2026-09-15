# 🚀 Linux Agent - Advanced System Integration

## Overview

Modul **Linux Agent** yang memberikan kemampuan **tanpa batas** kepada agent AI untuk berinteraksi dengan sistem Linux Anda. Module ini dirancang untuk canggih, aman (dalam batas permission user), dan mudah digunakan.

## ⚠️ Security Warning

Module ini memberikan akses **FULL SYSTEM ACCESS** sesuai dengan permission user yang menjalankan. 
- Hanya gunakan di lingkungan terpercaya
- Jangan expose ke publik tanpa authentication
- Agent dapat membaca/menulis file, execute commands, manage processes

## Features

### 🔧 7 Advanced Tools

| Tool | Category | Description |
|------|----------|-------------|
| `linux_shell_execute` | system | Execute ANY shell command with full environment |
| `linux_file_read` | filesystem | Read any accessible file (text/binary) |
| `linux_file_write` | filesystem | Write/create files anywhere user has permission |
| `linux_directory_list` | filesystem | List directory contents recursively with metadata |
| `linux_process_manager` | system | Kill, terminate, pause, resume processes |
| `linux_system_info` | system | Get comprehensive system information |
| `linux_network_scan` | network | TCP port scanning |

## Installation

Module sudah terintegrasi dalam project. Cukup import:

```python
from packages.core.tools import linux_agent
from packages.core.tools import registry
```

Tools akan otomatis terdaftar saat module di-import.

## Usage Examples

### 1. Execute Shell Commands

```python
import asyncio
from packages.core.tools import registry

async def run_command():
    # Simple command
    result = await registry.execute_tool('linux_shell_execute', 
                                         command='ls -la /home')
    print(result.output['stdout'])
    
    # Complex pipeline
    result = await registry.execute_tool('linux_shell_execute',
                                         command='ps aux | grep python | wc -l')
    print(f"Python processes: {result.output['stdout']}")
    
    # With timeout and custom working directory
    result = await registry.execute_tool('linux_shell_execute',
                                         command='npm install',
                                         timeout=120,
                                         cwd='/workspace/apps/frontend')

asyncio.run(run_command())
```

### 2. File Operations

```python
# Read a file
result = await registry.execute_tool('linux_file_read',
                                     path='/etc/hostname')
print(f"Hostname: {result.output}")

# Read binary file
result = await registry.execute_tool('linux_file_read',
                                     path='/path/to/image.png',
                                     binary=True)
# Returns hex string

# Write a file
result = await registry.execute_tool('linux_file_write',
                                     path='/tmp/myfile.txt',
                                     content='Hello World!')

# Append to file
result = await registry.execute_tool('linux_file_write',
                                     path='/var/log/app.log',
                                     content='New log entry\n',
                                     append=True)
```

### 3. Directory Management

```python
# List directory
result = await registry.execute_tool('linux_directory_list',
                                     path='/workspace',
                                     recursive=False)
for item in result.output:
    print(f"{item['name']} - {item['type']} ({item['size']} bytes)")

# Recursive listing
result = await registry.execute_tool('linux_directory_list',
                                     path='/workspace/packages',
                                     recursive=True)
print(f"Total items: {result.metadata['count']}")
```

### 4. Process Management

```python
# Get process info by PID
result = await registry.execute_tool('linux_process_manager',
                                     action='info',
                                     identifier=1234)
print(result.output)

# Kill process by name
result = await registry.execute_tool('linux_process_manager',
                                     action='kill',
                                     identifier='python3')

# Pause/Resume
await registry.execute_tool('linux_process_manager',
                           action='pause',
                           identifier=5678)

await registry.execute_tool('linux_process_manager',
                           action='resume',
                           identifier=5678)
```

### 5. System Information

```python
result = await registry.execute_tool('linux_system_info')
info = result.output

print(f"Platform: {info['platform']}")
print(f"CPU Cores: {info['cpu_count']}")
print(f"Memory: {info['memory']['available'] / 1024**2:.2f} MB available")
print(f"User: {info['user']}")
```

### 6. Network Scanning

```python
# Scan common ports on localhost
result = await registry.execute_tool('linux_network_scan',
                                     host='127.0.0.1',
                                     ports=[22, 80, 443, 8080, 3306],
                                     timeout=1.0)
print(f"Open ports: {result.output}")

# Scan remote host
result = await registry.execute_tool('linux_network_scan',
                                     host='192.168.1.1',
                                     ports=range(1, 1024))
```

## Advanced Usage

### Chaining Commands

```python
# Create a backup script
commands = [
    'mkdir -p /backups',
    'tar -czf /backups/workspace_$(date +%Y%m%d).tar.gz /workspace',
    'ls -lh /backups/'
]

for cmd in commands:
    result = await registry.execute_tool('linux_shell_execute', command=cmd)
    if result.success:
        print(result.output['stdout'])
    else:
        print(f"Error: {result.output['stderr']}")
```

### Monitoring System Resources

```python
import time

async def monitor_system():
    for i in range(5):
        result = await registry.execute_tool('linux_system_info')
        mem_percent = result.output['memory']['percent']
        print(f"[{i}] Memory Usage: {mem_percent}%")
        await asyncio.sleep(2)

asyncio.run(monitor_system())
```

### Process Hunting

```python
async def find_and_kill_zombies():
    # Find all zombie processes
    result = await registry.execute_tool('linux_shell_execute',
                                         command='ps aux | awk \'$8=="Z" {print $2}\'')
    
    if result.output['stdout'].strip():
        pids = result.output['stdout'].strip().split('\n')
        for pid in pids:
            await registry.execute_tool('linux_process_manager',
                                       action='kill',
                                       identifier=int(pid))
            print(f"Killed zombie process {pid}")
```

## API Reference

### LinuxSystemTools (Static Class)

Direct access without registry:

```python
from packages.core.tools import LinuxSystemTools

# Direct method calls
result = LinuxSystemTools.execute_shell_command('whoami')
print(result.stdout)

files = LinuxSystemTools.list_directory('/tmp')
print(files['contents'])
```

### ToolResult Structure

```python
{
    "success": bool,
    "output": Any,      # Tool-specific output
    "error": str,       # Error message if failed
    "metadata": dict    # Additional context
}
```

## Best Practices

1. **Timeout Settings**: Always set appropriate timeouts for long-running commands
2. **Error Handling**: Check `result.success` before using output
3. **Path Validation**: Validate paths before file operations
4. **Resource Limits**: Be mindful of system resources when scanning or processing
5. **Logging**: Log important operations for audit trails

## Architecture

```
packages/core/tools/
├── linux_system.py    # Core system interaction utilities
├── linux_agent.py     # Tool wrappers for agent registry
├── registry.py        # Tool registration system
└── __init__.py        # Package exports
```

## License

Internal use only. Handle with care.

---

**🎯 Agent sekarang memiliki kekuatan penuh untuk bekerja tanpa batas pada sistem Linux Anda!**
