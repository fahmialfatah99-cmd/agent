"""
Agent Loop Module
=================
Main agent loop that orchestrates Planner → Reasoner → Executor → Reflector.
"""

from typing import Optional, Dict, Any, List, AsyncIterator
from pydantic import BaseModel, Field
from enum import Enum

from .planner import Planner, Plan
from .reasoner import Reasoner, ReasoningTrace
from .executor import Executor, ExecutionResult
from .reflector import Reflector, Reflection

import asyncio


async def with_overall_timeout(
    agen: AsyncIterator[Dict[str, Any]],
    timeout: float,
) -> AsyncIterator[Dict[str, Any]]:
    """Wrap an async generator with an overall wall-clock timeout."""
    import time as time_mod

    deadline = time_mod.monotonic() + timeout
    while True:
        remaining = deadline - time_mod.monotonic()
        if remaining <= 0:
            yield {"event": "error", "error": f"Agent run timed out after {timeout} seconds"}
            return
        try:
            item = await asyncio.wait_for(agen.__anext__(), timeout=remaining)
        except StopAsyncIteration:
            return
        except (asyncio.TimeoutError, asyncio.CancelledError):
            yield {"event": "error", "error": f"Agent run timed out after {timeout} seconds"}
            return
        yield item


class AgentState(str, Enum):
    """Agent state enumeration."""
    IDLE = "idle"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentLoopConfig(BaseModel):
    """Configuration for the agent loop."""
    max_iterations: int = 10
    max_reflections: int = 5
    enable_reflection: bool = True
    enable_self_correction: bool = True
    verbose: bool = False
    timeout_per_step: float = 30.0
    overall_timeout: float = 120.0


class AgentLoop:
    """
    Main agent loop implementing ReAct + Reflection pattern.
    
    Flow:
    1. Receive goal/task
    2. Plan (break down into steps)
    3. Reason (analyze current situation)
    4. Execute (perform action)
    5. Reflect (learn from outcome)
    6. Repeat until goal achieved or max iterations
    """

    def __init__(
        self,
        provider,
        tool_registry=None,
        config: Optional[AgentLoopConfig] = None
    ):
        """Initialize the agent loop."""
        self.provider = provider
        self.config = config or AgentLoopConfig()
        
        # Initialize components
        self.planner = Planner(provider)
        self.reasoner = Reasoner(provider)
        self.executor = Executor(tool_registry, timeout=self.config.timeout_per_step)
        self.reflector = Reflector(provider)
        
        # State
        self.state = AgentState.IDLE
        self.current_plan: Optional[Plan] = None
        self.current_goal: str = ""
        self.iteration_count = 0
        self._conversation_history: List[Dict[str, str]] = []

    async def run(
        self,
        goal: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the agent loop to achieve a goal, bounded by overall_timeout."""
        try:
            return await asyncio.wait_for(
                self._run_inner(goal, context),
                timeout=self.config.overall_timeout
            )
        except asyncio.TimeoutError:
            self.state = AgentState.FAILED
            return {
                "success": False,
                "error": f"Agent run timed out after {self.config.overall_timeout} seconds",
                "plan": self.current_plan.to_dict() if self.current_plan else None,
            }

    async def _run_inner(
        self,
        goal: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the agent loop to achieve a goal."""
        import asyncio

        self.state = AgentState.THINKING
        self.current_goal = goal
        self.iteration_count = 0
        
        try:
            # Step 1: Create initial plan
            self.state = AgentState.PLANNING
            self.current_plan = await self.planner.create_plan(goal, context)
            
            if self.config.verbose:
                print(f"Created plan with {len(self.current_plan.steps)} steps")
            
            # Step 2: Execute plan steps
            self.state = AgentState.EXECUTING
            
            while not self.current_plan.is_complete():
                if self.iteration_count >= self.config.max_iterations:
                    self.state = AgentState.FAILED
                    return {
                        "success": False,
                        "error": "Max iterations reached",
                        "plan": self.current_plan.to_dict()
                    }
                
                self.iteration_count += 1
                
                # Get current step
                current_step = self.current_plan.get_current_step()
                if not current_step:
                    break
                
                # Reason about current step
                self.state = AgentState.THINKING
                reasoning = await asyncio.wait_for(
                    self.reasoner.reason(
                        situation=current_step.description,
                        context=context
                    ),
                    timeout=self.config.timeout_per_step
                )
                
                if self.config.verbose:
                    print(f"Reasoning: {reasoning.decision}")
                
                # Execute the step
                self.state = AgentState.EXECUTING
                result = await self.executor.execute_plan_step(
                    step_description=current_step.description,
                    tool_name=current_step.tool_name,
                    tool_args=current_step.tool_args,
                    timeout=self.config.timeout_per_step
                )
                
                if result.success:
                    self.current_plan.mark_step_complete(current_step.id, result.output)
                    
                    # Reflect on success
                    if self.config.enable_reflection:
                        self.state = AgentState.REFLECTING
                        await asyncio.wait_for(
                            self.reflector.reflect(
                                action=current_step.description,
                                outcome=result.output,
                                success=True
                            ),
                            timeout=self.config.timeout_per_step
                        )
                else:
                    self.current_plan.mark_step_failed(current_step.id, result.error)
                    
                    # Reflect on failure and potentially revise plan
                    if self.config.enable_reflection and self.config.enable_self_correction:
                        self.state = AgentState.REFLECTING
                        reflection = await asyncio.wait_for(
                            self.reflector.reflect(
                                action=current_step.description,
                                outcome=result.error,
                                success=False
                            ),
                            timeout=self.config.timeout_per_step
                        )
                        
                        # Revise plan based on reflection
                        feedback = f"Step failed: {result.error}. Suggestions: {reflection.improvements}"
                        self.current_plan = await asyncio.wait_for(
                            self.planner.revise_plan(
                                self.current_plan,
                                feedback
                            ),
                            timeout=self.config.timeout_per_step
                        )
                    
                    if not self.config.enable_self_correction:
                        self.state = AgentState.FAILED
                        return {
                            "success": False,
                            "error": result.error,
                            "plan": self.current_plan.to_dict()
                        }
                
                # Advance to next step
                self.current_plan.advance()
            
            self.state = AgentState.COMPLETED
            
            return {
                "success": True,
                "goal": goal,
                "plan": self.current_plan.to_dict(),
                "iterations": self.iteration_count,
                "execution_history": [
                    r.dict() for r in self.executor.get_execution_history()
                ]
            }
            
        except asyncio.TimeoutError:
            self.state = AgentState.FAILED
            return {
                "success": False,
                "error": f"Step timed out after {self.config.timeout_per_step} seconds",
                "plan": self.current_plan.to_dict() if self.current_plan else None
            }
        except Exception as e:
            self.state = AgentState.FAILED
            return {
                "success": False,
                "error": str(e),
                "plan": self.current_plan.to_dict() if self.current_plan else None
            }

    async def run_streaming(
        self,
        goal: str,
        context: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Run the agent loop with streaming updates, bounded by overall_timeout."""
        agen = self._stream_events(goal, context)
        async for event in with_overall_timeout(
            agen, self.config.overall_timeout
        ):
            yield event

    async def _stream_events(
        self,
        goal: str,
        context: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Run the agent loop with streaming updates."""
        import asyncio

        self.state = AgentState.THINKING
        self.current_goal = goal
        self.iteration_count = 0
        
        yield {
            "event": "start",
            "goal": goal,
            "state": self.state.value
        }
        
        try:
            # Create plan
            self.state = AgentState.PLANNING
            yield {
                "event": "planning_start",
                "state": self.state.value
            }
            
            self.current_plan = await asyncio.wait_for(
                self.planner.create_plan(goal, context),
                timeout=self.config.timeout_per_step
            )
            
            yield {
                "event": "plan_created",
                "plan": self.current_plan.to_dict(),
                "step_count": len(self.current_plan.steps)
            }
            
            # Execute steps
            self.state = AgentState.EXECUTING
            
            while not self.current_plan.is_complete():
                if self.iteration_count >= self.config.max_iterations:
                    self.state = AgentState.FAILED
                    yield {
                        "event": "error",
                        "error": "Max iterations reached"
                    }
                    return
                
                self.iteration_count += 1
                current_step = self.current_plan.get_current_step()
                
                if not current_step:
                    break
                
                # Reasoning
                self.state = AgentState.THINKING
                yield {
                    "event": "reasoning_start",
                    "step": current_step.description
                }
                
                reasoning = await asyncio.wait_for(
                    self.reasoner.reason(
                        situation=current_step.description,
                        context=context
                    ),
                    timeout=self.config.timeout_per_step
                )
                
                yield {
                    "event": "reasoning_complete",
                    "reasoning": reasoning.dict()
                }
                
                # Execution
                self.state = AgentState.EXECUTING
                yield {
                    "event": "execution_start",
                    "tool": current_step.tool_name
                }
                
                result = await self.executor.execute_plan_step(
                    step_description=current_step.description,
                    tool_name=current_step.tool_name,
                    tool_args=current_step.tool_args,
                    timeout=self.config.timeout_per_step
                )
                
                yield {
                    "event": "execution_complete" if result.success else "execution_failed",
                    "result": result.dict()
                }
                
                if result.success:
                    self.current_plan.mark_step_complete(current_step.id, result.output)
                else:
                    self.current_plan.mark_step_failed(current_step.id, result.error)
                    
                    if self.config.enable_self_correction:
                        self.state = AgentState.REFLECTING
                        reflection = await asyncio.wait_for(
                            self.reflector.reflect(
                                action=current_step.description,
                                outcome=result.error,
                                success=False
                            ),
                            timeout=self.config.timeout_per_step
                        )
                        
                        yield {
                            "event": "reflection",
                            "reflection": reflection.dict()
                        }
                        
                        self.current_plan = await asyncio.wait_for(
                            self.planner.revise_plan(
                                self.current_plan,
                                f"Step failed: {result.error}"
                            ),
                            timeout=self.config.timeout_per_step
                        )
                    else:
                        self.state = AgentState.FAILED
                        yield {
                            "event": "error",
                            "error": result.error
                        }
                        return
                
                self.current_plan.advance()
            
            self.state = AgentState.COMPLETED
            yield {
                "event": "complete",
                "plan": self.current_plan.to_dict(),
                "iterations": self.iteration_count
            }
            
        except asyncio.TimeoutError:
            self.state = AgentState.FAILED
            yield {
                "event": "error",
                "error": f"Step timed out after {self.config.timeout_per_step} seconds"
            }
        except Exception as e:
            self.state = AgentState.FAILED
            yield {
                "event": "error",
                "error": str(e)
            }

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return {
            "state": self.state.value,
            "goal": self.current_goal,
            "iteration": self.iteration_count,
            "plan": self.current_plan.to_dict() if self.current_plan else None,
            "available_tools": self.executor.get_available_tools()
        }

    def reset(self) -> None:
        """Reset the agent loop."""
        self.state = AgentState.IDLE
        self.current_plan = None
        self.current_goal = ""
        self.iteration_count = 0
        self._conversation_history.clear()
