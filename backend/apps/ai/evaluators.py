from dataclasses import dataclass
from decimal import Decimal
from time import perf_counter
from typing import Any, Protocol

from .models import AIAssessment
from .providers import OpenAIProvider
from .services import (
    complete_assessment,
    fail_assessment,
    start_assessment,
)


class AIProvider(Protocol):
    def evaluate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        ...


@dataclass
class EvaluationResult:
    overall_score: Decimal
    task_achievement: Decimal
    coherence_cohesion: Decimal
    lexical_resource: Decimal
    grammar_accuracy: Decimal
    feedback: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    raw_response: dict[str, Any]
    processing_time_ms: int


WRITING_SYSTEM_PROMPT = """
You are an expert IELTS Writing examiner.

Evaluate the student's writing according to IELTS Writing
assessment criteria.

Assess:

1. Task Achievement
2. Coherence and Cohesion
3. Lexical Resource
4. Grammatical Range and Accuracy

Use IELTS-style band scores from 0.0 to 9.0.

The overall score must be between 0.0 and 9.0.

Each criterion score must also be between 0.0 and 9.0.

Be strict, evidence-based, and specific.

Do not invent information that is not present in the
student's response.

Return structured evaluation data only.
"""


class AIEvaluationError(Exception):
    """Raised when an assessment cannot be evaluated."""


class WritingEvaluator:
    def __init__(
        self,
        provider: AIProvider | None = None,
    ) -> None:
        self.provider = provider or OpenAIProvider()

    def build_prompt(
        self,
        assessment: AIAssessment,
    ) -> str:
        return f"""
Evaluate the following IELTS Writing response.

Task / prompt:
{assessment.source_text}

Student response:
{assessment.task_response}

Return:

- overall IELTS band score
- feedback
- strengths
- weaknesses
- concrete improvement suggestions
- four criterion scores:
  Task Achievement
  Coherence and Cohesion
  Lexical Resource
  Grammatical Range and Accuracy

The evaluation must be based only on the supplied task
and student response.
"""

    def evaluate(
        self,
        assessment: AIAssessment,
    ) -> EvaluationResult:
        started_at = perf_counter()

        response = self.provider.evaluate(
            system_prompt=WRITING_SYSTEM_PROMPT,
            user_prompt=self.build_prompt(assessment),
        )

        processing_time_ms = int(
            (perf_counter() - started_at) * 1000
        )

        try:
            overall_score = Decimal(
                str(response['overall_score'])
            )

            feedback = str(
                response['feedback']
            )

            strengths = [
                str(item)
                for item in response['strengths']
            ]

            weaknesses = [
                str(item)
                for item in response['weaknesses']
            ]

            suggestions = [
                str(item)
                for item in response['suggestions']
            ]

            criteria = response['criteria']

            task_achievement = Decimal(
                str(criteria['task_achievement'])
            )

            coherence_cohesion = Decimal(
                str(criteria['coherence_cohesion'])
            )

            lexical_resource = Decimal(
                str(criteria['lexical_resource'])
            )

            grammar_accuracy = Decimal(
                str(criteria['grammar_accuracy'])
            )

            criterion_scores = {
                'task_achievement': task_achievement,
                'coherence_cohesion': coherence_cohesion,
                'lexical_resource': lexical_resource,
                'grammar_accuracy': grammar_accuracy,
            }

            for key, score in criterion_scores.items():
                if not Decimal('0') <= score <= Decimal('9'):
                    raise AIEvaluationError(
                        f'Invalid IELTS criterion score: {key}.'
                    )

        except AIEvaluationError:
            raise

        except (
            KeyError,
            TypeError,
            ValueError,
            ArithmeticError,
        ) as exc:
            raise AIEvaluationError(
                f'Invalid AI evaluation response: {exc}'
            ) from exc

        if not Decimal('0') <= overall_score <= Decimal('9'):
            raise AIEvaluationError(
                'AI returned an invalid IELTS band score.'
            )

        return EvaluationResult(
            overall_score=overall_score,
            task_achievement=task_achievement,
            coherence_cohesion=coherence_cohesion,
            lexical_resource=lexical_resource,
            grammar_accuracy=grammar_accuracy,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            raw_response=response,
            processing_time_ms=processing_time_ms,
        )


def evaluate_assessment(
    assessment: AIAssessment,
    provider: AIProvider | None = None,
) -> AIAssessment:
    assessment = start_assessment(assessment)

    try:
        if assessment.skill == AIAssessment.Skill.WRITING:
            evaluator = WritingEvaluator(
                provider=provider,
            )
        else:
            raise AIEvaluationError(
                f'No evaluator implemented for skill '
                f'{assessment.skill}.'
            )

        result = evaluator.evaluate(
            assessment
        )

        return complete_assessment(
            assessment=assessment,
            overall_score=result.overall_score,
            task_achievement=result.task_achievement,
            coherence_cohesion=result.coherence_cohesion,
            lexical_resource=result.lexical_resource,
            grammar_accuracy=result.grammar_accuracy,
            feedback=result.feedback,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            suggestions=result.suggestions,
            raw_response=result.raw_response,
            processing_time_ms=result.processing_time_ms,
        )

    except Exception as exc:
        return fail_assessment(
            assessment=assessment,
            error_message=str(exc),
        )
