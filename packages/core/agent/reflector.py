"""
Reflector Module
================
Responsible for self-reflection and learning from past actions.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Reflection(BaseModel):
    """A reflection on past actions."""
    action_taken: str
    outcome: str
    success: bool
    lessons_learned: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    patterns_identified: List[str] = Field(default_factory=list)
    confidence_adjustment: float = 0.0  # How much to adjust confidence
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Reflector:
    """
    Reflector component that analyzes past actions for continuous improvement.
    Implements self-reflection and meta-learning.
    """

    def __init__(self, provider):
        """Initialize reflector with an LLM provider."""
        self.provider = provider
        self._reflection_history: List[Reflection] = []
        self.system_prompt = """You are an expert reflector. Your task is to analyze past actions and outcomes to extract learnings.

For each action-outcome pair, provide:
1. Lessons learned from the experience
2. Suggested improvements for future similar situations
3. Patterns you notice (if any)
4. Confidence adjustment (positive or negative)

Respond in JSON format:
{
    "lessons_learned": ["lesson 1", "lesson 2"],
    "improvements": ["improvement 1", "improvement 2"],
    "patterns_identified": ["pattern 1"],
    "confidence_adjustment": 0.1
}"""

    async def reflect(
        self,
        action: str,
        outcome: str,
        success: bool,
        context: Optional[str] = None
    ) -> Reflection:
        """Reflect on a completed action."""
        from ..providers.base import Message

        user_message = f"""Action taken: {action}
Outcome: {outcome}
Success: {"Yes" if success else "No"}"""

        if context:
            user_message += f"\n\nContext: {context}"

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message)
        ]

        response = await self.provider.chat_completion(messages)
        content = response.choices[0]["message"]["content"]

        try:
            import json
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                reflection_data = json.loads(json_str)
            else:
                reflection_data = json.loads(content)

            reflection = Reflection(
                action_taken=action,
                outcome=outcome,
                success=success,
                lessons_learned=reflection_data.get("lessons_learned", []),
                improvements=reflection_data.get("improvements", []),
                patterns_identified=reflection_data.get("patterns_identified", []),
                confidence_adjustment=reflection_data.get("confidence_adjustment", 0.0)
            )

            self._reflection_history.append(reflection)
            return reflection

        except Exception:
            # Fallback
            reflection = Reflection(
                action_taken=action,
                outcome=outcome,
                success=success,
                lessons_learned=["Analyze this action for future improvements"],
                improvements=["Consider alternative approaches"],
                confidence_adjustment=-0.05 if not success else 0.05
            )
            self._reflection_history.append(reflection)
            return reflection

    async def batch_reflect(
        self,
        actions_outcomes: List[Dict[str, Any]]
    ) -> List[Reflection]:
        """Reflect on multiple actions at once."""
        reflections = []
        for item in actions_outcomes:
            reflection = await self.reflect(
                action=item.get("action", ""),
                outcome=item.get("outcome", ""),
                success=item.get("success", False),
                context=item.get("context")
            )
            reflections.append(reflection)
        return reflections

    def get_reflection_history(
        self,
        limit: Optional[int] = None,
        filter_by_success: Optional[bool] = None
    ) -> List[Reflection]:
        """Get reflection history with optional filtering."""
        history = self._reflection_history.copy()
        
        if filter_by_success is not None:
            history = [r for r in history if r.success == filter_by_success]
        
        if limit:
            history = history[-limit:]
        
        return history

    def get_aggregate_insights(self) -> Dict[str, Any]:
        """Get aggregated insights from all reflections."""
        if not self._reflection_history:
            return {
                "total_reflections": 0,
                "success_rate": 0.0,
                "common_lessons": [],
                "common_improvements": [],
                "average_confidence_adjustment": 0.0
            }

        total = len(self._reflection_history)
        successes = sum(1 for r in self._reflection_history if r.success)
        
        # Collect all lessons and improvements
        all_lessons = []
        all_improvements = []
        all_patterns = []
        
        for reflection in self._reflection_history:
            all_lessons.extend(reflection.lessons_learned)
            all_improvements.extend(reflection.improvements)
            all_patterns.extend(reflection.patterns_identified)

        # Find most common items
        from collections import Counter
        lesson_counts = Counter(all_lessons)
        improvement_counts = Counter(all_improvements)
        pattern_counts = Counter(all_patterns)

        avg_confidence = (
            sum(r.confidence_adjustment for r in self._reflection_history) / total
        )

        return {
            "total_reflections": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "common_lessons": [item for item, _ in lesson_counts.most_common(5)],
            "common_improvements": [item for item, _ in improvement_counts.most_common(5)],
            "common_patterns": [item for item, _ in pattern_counts.most_common(5)],
            "average_confidence_adjustment": avg_confidence
        }

    async def generate_meta_learning(self) -> str:
        """Generate meta-learning summary from all reflections."""
        from ..providers.base import Message

        insights = self.get_aggregate_insights()
        
        history_str = "\n".join([
            f"- Action: {r.action_taken}\n  Outcome: {r.outcome}\n  Lessons: {r.lessons_learned}"
            for r in self._reflection_history[-10:]  # Last 10 reflections
        ])

        user_message = f"""Based on these reflections:
{history_str}

And aggregate insights:
- Success Rate: {insights['success_rate']:.2%}
- Common Lessons: {insights['common_lessons']}
- Common Improvements: {insights['common_improvements']}

Provide a meta-learning summary with key takeaways and strategic recommendations."""

        messages = [
            Message(role="system", content="You are a meta-learning expert. Synthesize learnings into actionable insights."),
            Message(role="user", content=user_message)
        ]

        response = await self.provider.chat_completion(messages)
        return response.choices[0]["message"]["content"]

    def clear_history(self) -> None:
        """Clear reflection history."""
        self._reflection_history.clear()
