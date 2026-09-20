import json
from typing import Any

from django.conf import settings
from openai import OpenAI


class AIProviderError(Exception):
    """Raised when an AI provider cannot complete an evaluation."""


class OpenAIProvider:
    """OpenAI provider used by the IELTS AI evaluation layer."""

    def __init__(self) -> None:
        api_key = settings.OPENAI_API_KEY

        if not api_key:
            raise AIProviderError(
                'OPENAI_API_KEY is not configured.'
            )

        self.client = OpenAI(api_key=api_key)
        self.model = settings.OPENAI_MODEL

    def evaluate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        'role': 'system',
                        'content': system_prompt,
                    },
                    {
                        'role': 'user',
                        'content': user_prompt,
                    },
                ],
                text={
                    'format': {
                        'type': 'json_schema',
                        'name': 'ielts_evaluation',
                        'strict': True,
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'overall_score': {
                                    'type': 'number',
                                },
                                'feedback': {
                                    'type': 'string',
                                },
                                'strengths': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string',
                                    },
                                },
                                'weaknesses': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string',
                                    },
                                },
                                'suggestions': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string',
                                    },
                                },
                                'criteria': {
                                    'type': 'object',
                                    'properties': {
                                        'task_achievement': {
                                            'type': 'number',
                                        },
                                        'coherence_cohesion': {
                                            'type': 'number',
                                        },
                                        'lexical_resource': {
                                            'type': 'number',
                                        },
                                        'grammar_accuracy': {
                                            'type': 'number',
                                        },
                                    },
                                    'required': [
                                        'task_achievement',
                                        'coherence_cohesion',
                                        'lexical_resource',
                                        'grammar_accuracy',
                                    ],
                                    'additionalProperties': False,
                                },
                            },
                            'required': [
                                'overall_score',
                                'feedback',
                                'strengths',
                                'weaknesses',
                                'suggestions',
                                'criteria',
                            ],
                            'additionalProperties': False,
                        },
                    },
                },
            )

            output_text = response.output_text

            if not output_text:
                raise AIProviderError(
                    'OpenAI returned an empty response.'
                )

            result = json.loads(output_text)

            if not isinstance(result, dict):
                raise AIProviderError(
                    'OpenAI returned an invalid JSON object.'
                )

            return result

        except AIProviderError:
            raise

        except json.JSONDecodeError as exc:
            raise AIProviderError(
                f'OpenAI returned invalid JSON: {exc}'
            ) from exc

        except Exception as exc:
            raise AIProviderError(
                f'OpenAI request failed: {exc}'
            ) from exc


class MockAIProvider:
    """
    Local AI provider used for development and automated tests.

    It never makes network requests and never consumes API credits.
    """

    def evaluate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        return {
            'overall_score': 6.5,
            'feedback': (
                'The response addresses the task clearly and presents '
                'both views with a relevant conclusion. The ideas are '
                'generally well organised, although some points could '
                'be developed in greater depth.'
            ),
            'strengths': [
                'The response addresses both sides of the discussion.',
                'The main position is clearly stated.',
                'Paragraphing is logical and easy to follow.',
            ],
            'weaknesses': [
                'Some ideas could be developed with more specific examples.',
                'Vocabulary could be more varied in places.',
                'Some grammatical structures could be more complex.',
            ],
            'suggestions': [
                'Develop each main idea with a specific explanation or example.',
                'Use a wider range of precise academic vocabulary.',
                'Include more complex sentence structures where appropriate.',
            ],
            'criteria': {
                'task_achievement': 6.5,
                'coherence_cohesion': 6.5,
                'lexical_resource': 6.5,
                'grammar_accuracy': 6.0,
            },
        }
