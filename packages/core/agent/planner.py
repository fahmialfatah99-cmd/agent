"""
Planner Module
==============
Responsible for breaking down complex tasks into actionable steps.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json


class PlanStep(BaseModel):
    """Individual step in a plan."""
    id: int
    description: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    error: Optional[str] = None


class Plan(BaseModel):
    """Complete plan for achieving a goal."""
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    status: str = "active"  # active, completed, failed, cancelled
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_step(self, description: str, tool_name: Optional[str] = None, 
                 tool_args: Optional[Dict[str, Any]] = None) -> PlanStep:
        """Add a new step to the plan."""
        step = PlanStep(
            id=len(self.steps),
            description=description,
            tool_name=tool_name,
            tool_args=tool_args
        )
        self.steps.append(step)
        return step

    def get_current_step(self) -> Optional[PlanStep]:
        """Get the current step to execute."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def mark_step_complete(self, step_id: int, result: str) -> None:
        """Mark a step as completed."""
        for step in self.steps:
            if step.id == step_id:
                step.status = "completed"
                step.result = result
                break

    def mark_step_failed(self, step_id: int, error: str) -> None:
        """Mark a step as failed."""
        for step in self.steps:
            if step.id == step_id:
                step.status = "failed"
                step.error = error
                break

    def advance(self) -> bool:
        """Advance to the next step."""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        self.status = "completed"
        return False

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(step.status == "completed" for step in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary."""
        return {
            "goal": self.goal,
            "steps": [step.dict() for step in self.steps],
            "current_step_index": self.current_step_index,
            "status": self.status,
            "metadata": self.metadata
        }


class Planner:
    """
    Planner component that breaks down goals into executable steps.
    Uses LLM to generate structured plans.
    """

    def __init__(self, provider):
        """Initialize planner with an LLM provider."""
        self.provider = provider
        self.system_prompt = """You are an expert planner. Your task is to break down complex goals into clear, actionable steps.

For each goal, create a detailed plan with:
1. Clear, sequential steps
2. Identify which tools (if any) are needed for each step
3. Consider potential obstacles and alternatives

Respond in JSON format with this structure:
{
    "goal": "restated goal",
    "steps": [
        {
            "description": "what to do",
            "tool_name": "tool to use or null",
            "tool_args": {"arg1": "value1"} or null
        }
    ]
}"""

    async def create_plan(self, goal: str, context: Optional[str] = None) -> Plan:
        """Create a plan for achieving the given goal."""
        from ..providers.base import Message

        user_message = f"Goal: {goal}"
        if context:
            user_message += f"\n\nContext: {context}"

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message)
        ]

        response = await self.provider.chat_completion(messages)
        content = response.choices[0]["message"]["content"]

        # Parse the JSON response
        try:
            # Try to extract JSON from the response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                plan_data = json.loads(json_str)
            else:
                plan_data = json.loads(content)

            plan = Plan(goal=plan_data.get("goal", goal))
            
            for i, step_data in enumerate(plan_data.get("steps", [])):
                plan.add_step(
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool_name"),
                    tool_args=step_data.get("tool_args")
                )

            return plan

        except json.JSONDecodeError as e:
            # Fallback: create a simple plan
            plan = Plan(goal=goal)
            plan.add_step(description=f"Achieve goal: {goal}")
            return plan

    async def revise_plan(self, plan: Plan, feedback: str) -> Plan:
        """Revise an existing plan based on feedback."""
        from ..providers.base import Message

        current_plan_str = json.dumps(plan.to_dict(), indent=2)
        
        user_message = f"""Current Plan:
{current_plan_str}

Feedback: {feedback}

Please revise the plan based on the feedback. Respond in the same JSON format."""

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message)
        ]

        response = await self.provider.chat_completion(messages)
        content = response.choices[0]["message"]["content"]

        try:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                plan_data = json.loads(json_str)
            else:
                plan_data = json.loads(content)

            revised_plan = Plan(goal=plan_data.get("goal", plan.goal))
            
            for i, step_data in enumerate(plan_data.get("steps", [])):
                revised_plan.add_step(
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool_name"),
                    tool_args=step_data.get("tool_args")
                )

            return revised_plan

        except json.JSONDecodeError:
            return plan
