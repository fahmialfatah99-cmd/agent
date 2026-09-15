"""
Reasoner Module
===============
Responsible for analyzing situations and making decisions.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReasoningTrace(BaseModel):
    """Record of the reasoning process."""
    observation: str
    analysis: str
    hypothesis: List[str] = Field(default_factory=list)
    decision: str
    confidence: float = 0.0  # 0.0 to 1.0
    alternatives_considered: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Reasoner:
    """
    Reasoner component that analyzes situations and makes decisions.
    Uses chain-of-thought reasoning with reflection.
    """

    def __init__(self, provider):
        """Initialize reasoner with an LLM provider."""
        self.provider = provider
        self.system_prompt = """You are an expert reasoner. Your task is to analyze situations carefully and make well-reasoned decisions.

For each situation, provide:
1. Observation: What you observe from the current state
2. Analysis: Deep analysis of the situation
3. Hypothesis: Possible explanations or approaches
4. Decision: Your final decision with justification
5. Confidence: How confident you are (0.0 to 1.0)
6. Alternatives: Other options you considered

Respond in JSON format with this structure:
{
    "observation": "what you observe",
    "analysis": "your analysis",
    "hypothesis": ["hypothesis 1", "hypothesis 2"],
    "decision": "your decision",
    "confidence": 0.85,
    "alternatives_considered": ["alternative 1", "alternative 2"]
}"""

    async def reason(
        self,
        situation: str,
        context: Optional[str] = None,
        available_tools: Optional[List[str]] = None
    ) -> ReasoningTrace:
        """Analyze a situation and produce a reasoning trace."""
        from ..providers.base import Message

        user_message = f"Situation: {situation}"
        
        if context:
            user_message += f"\n\nContext: {context}"
        
        if available_tools:
            tools_str = ", ".join(available_tools)
            user_message += f"\n\nAvailable tools: {tools_str}"

        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=user_message)
        ]

        response = await self.provider.chat_completion(messages)
        content = response.choices[0]["message"]["content"]

        # Parse the JSON response
        try:
            import json
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                reasoning_data = json.loads(json_str)
            else:
                reasoning_data = json.loads(content)

            return ReasoningTrace(
                observation=reasoning_data.get("observation", ""),
                analysis=reasoning_data.get("analysis", ""),
                hypothesis=reasoning_data.get("hypothesis", []),
                decision=reasoning_data.get("decision", ""),
                confidence=reasoning_data.get("confidence", 0.5),
                alternatives_considered=reasoning_data.get("alternatives_considered", [])
            )

        except Exception:
            # Fallback
            return ReasoningTrace(
                observation=situation,
                analysis="Unable to perform deep analysis",
                decision="Proceed with caution",
                confidence=0.5
            )

    async def evaluate_options(
        self,
        options: List[Dict[str, Any]],
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate multiple options and recommend the best one."""
        from ..providers.base import Message

        options_str = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        user_message = f"Evaluate these options:\n{options_str}"
        
        if criteria:
            criteria_str = ", ".join(criteria)
            user_message += f"\n\nEvaluation criteria: {criteria_str}"

        messages = [
            Message(role="system", content="""You are an expert evaluator. Compare the given options and recommend the best one based on the criteria.

Respond in JSON format:
{
    "evaluation": "detailed evaluation of each option",
    "recommended_option": index of best option (0-based),
    "reasoning": "why this option is best",
    "scores": [score for each option]
}"""),
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
                eval_data = json.loads(json_str)
            else:
                eval_data = json.loads(content)

            return {
                "evaluation": eval_data.get("evaluation", ""),
                "recommended_index": eval_data.get("recommended_option", 0),
                "reasoning": eval_data.get("reasoning", ""),
                "scores": eval_data.get("scores", [])
            }

        except Exception:
            return {
                "evaluation": "Unable to evaluate options",
                "recommended_index": 0,
                "reasoning": "Default to first option",
                "scores": [0.5] * len(options)
            }

    async def check_consistency(
        self,
        statement: str,
        context: List[str]
    ) -> Dict[str, Any]:
        """Check if a statement is consistent with given context."""
        from ..providers.base import Message

        context_str = "\n".join([f"- {c}" for c in context])
        
        user_message = f"""Statement: {statement}

Context:
{context_str}

Is the statement consistent with the context? Explain any inconsistencies.

Respond in JSON format:
{
    "consistent": true/false,
    "explanation": "explanation",
    "inconsistencies": ["list of inconsistencies if any"]
}"""

        messages = [
            Message(role="system", content="You are a logic checker. Determine if statements are consistent with given context."),
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
                result = json.loads(json_str)
            else:
                result = json.loads(content)

            return {
                "consistent": result.get("consistent", False),
                "explanation": result.get("explanation", ""),
                "inconsistencies": result.get("inconsistencies", [])
            }

        except Exception:
            return {
                "consistent": True,
                "explanation": "Unable to verify consistency",
                "inconsistencies": []
            }
