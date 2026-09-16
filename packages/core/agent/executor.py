"""
Executor Module
===============
Responsible for executing actions and tools.
"""

from typing import List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field
import asyncio


class ExecutionResult(BaseModel):
    """Result of an execution."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    tool_name: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Executor:
    """
    Executor component that executes actions using available tools.
    """

    def __init__(self, tool_registry=None, timeout: float = 30.0):
        """Initialize executor with optional tool registry and default per-step timeout."""
        self.tool_registry = tool_registry
        self.timeout = timeout
        self._tools: Dict[str, Callable] = {}
        self._execution_history: List[ExecutionResult] = []
        if tool_registry:
            self.import_from_registry(tool_registry)

    def import_from_registry(self, tool_registry) -> int:
        """Import all tools from a ToolRegistry into the executor."""
        imported = 0
        for definition in tool_registry.list_tools():
            tool = tool_registry.get(definition.name)
            if tool:
                self._tools[definition.name] = tool.execute
                imported += 1
        return imported

    def register_tool(self, name: str, func: Callable) -> None:
        """Register a tool function."""
        self._tools[name] = func

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self._tools.keys())

    async def execute(
        self,
        action: str,
        args: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> ExecutionResult:
        """Execute an action with given arguments."""
        import time
        start_time = time.time()
        timeout = timeout if timeout is not None else self.timeout

        # Check if action is a registered tool
        if action in self._tools:
            try:
                tool_func = self._tools[action]
                
                # Handle both sync and async functions
                if asyncio.iscoroutinefunction(tool_func):
                    result = await asyncio.wait_for(
                        tool_func(**(args or {})),
                        timeout=timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, lambda: tool_func(**(args or {}))
                        ),
                        timeout=timeout
                    )

                execution_time = time.time() - start_time
                
                exec_result = ExecutionResult(
                    success=True,
                    output=str(result) if result else "Action executed successfully",
                    tool_name=action,
                    execution_time=execution_time
                )
                
                self._execution_history.append(exec_result)
                return exec_result

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                exec_result = ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {timeout} seconds",
                    tool_name=action,
                    execution_time=execution_time
                )
                self._execution_history.append(exec_result)
                return exec_result

            except Exception as e:
                execution_time = time.time() - start_time
                exec_result = ExecutionResult(
                    success=False,
                    error=str(e),
                    tool_name=action,
                    execution_time=execution_time
                )
                self._execution_history.append(exec_result)
                return exec_result

        # If not a registered tool, treat as direct code execution (if enabled)
        return ExecutionResult(
            success=False,
            error=f"Unknown action/tool: {action}"
        )

    async def execute_plan_step(
        self,
        step_description: str,
        tool_name: Optional[str],
        tool_args: Optional[Dict[str, Any]],
        timeout: Optional[float] = None
    ) -> ExecutionResult:
        """Execute a plan step."""
        if tool_name:
            return await self.execute(tool_name, tool_args, timeout=timeout)
        else:
            # For steps without explicit tools, use reasoning
            return ExecutionResult(
                success=True,
                output=f"Step completed: {step_description}"
            )

    def get_execution_history(
        self,
        limit: Optional[int] = None
    ) -> List[ExecutionResult]:
        """Get execution history."""
        if limit:
            return self._execution_history[-limit:]
        return self._execution_history.copy()

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()

    async def batch_execute(
        self,
        actions: List[Dict[str, Any]],
        parallel: bool = False
    ) -> List[ExecutionResult]:
        """Execute multiple actions."""
        if parallel:
            tasks = [
                self.execute(
                    action.get("action", ""),
                    action.get("args")
                )
                for action in actions
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            exec_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    exec_results.append(ExecutionResult(
                        success=False,
                        error=str(result),
                        tool_name=actions[i].get("action")
                    ))
                else:
                    exec_results.append(result)
            
            return exec_results
        else:
            results = []
            for action in actions:
                result = await self.execute(
                    action.get("action", ""),
                    action.get("args")
                )
                results.append(result)
                if not result.success:
                    break  # Stop on first failure
            return results
