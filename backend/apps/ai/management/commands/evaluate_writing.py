from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.ai.evaluators import AIEvaluationError, evaluate_assessment
from apps.ai.models import AIAssessment
from apps.ai.providers import MockAIProvider
from apps.ai.services import create_assessment
from apps.users.models import User


class Command(BaseCommand):
    help = 'Evaluate an IELTS Writing response using the AI evaluator.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            required=True,
            help='Username of the student.',
        )

        parser.add_argument(
            '--task',
            required=True,
            help='IELTS Writing task prompt.',
        )

        parser.add_argument(
            '--response',
            required=True,
            help='Student writing response.',
        )

        parser.add_argument(
            '--mock',
            action='store_true',
            help='Use the local mock provider without making an API request.',
        )

    def handle(self, *args, **options):
        username = options['username']
        task = options['task']
        response = options['response']
        use_mock = options['mock']

        try:
            user = User.objects.get(
                username=username,
            )
        except User.DoesNotExist as exc:
            raise CommandError(
                f'User "{username}" does not exist.'
            ) from exc

        if not task.strip():
            raise CommandError(
                'The IELTS task prompt cannot be empty.'
            )

        if not response.strip():
            raise CommandError(
                'The student response cannot be empty.'
            )

        assessment = create_assessment(
            user=user,
            skill=AIAssessment.Skill.WRITING,
            source_text=task,
            task_response=response,
        )

        self.stdout.write(
            self.style.WARNING(
                f'Created assessment #{assessment.id}.'
            )
        )

        if use_mock:
            provider = MockAIProvider()

            self.stdout.write(
                self.style.WARNING(
                    'Using MockAIProvider. '
                    'No OpenAI API request will be made.'
                )
            )
        else:
            provider = None

            self.stdout.write(
                'Sending the response to the AI evaluator...'
            )

        try:
            assessment = evaluate_assessment(
                assessment=assessment,
                provider=provider,
            )
        except AIEvaluationError as exc:
            raise CommandError(
                f'AI evaluation failed: {exc}'
            ) from exc

        if assessment.status == AIAssessment.Status.FAILED:
            raise CommandError(
                assessment.error_message
                or 'AI evaluation failed.'
            )

        score = assessment.overall_score

        if score is None:
            raise CommandError(
                'AI evaluation completed without an overall score.'
            )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'IELTS Writing evaluation completed.'
            )
        )
        self.stdout.write('')

        self.stdout.write(
            f'Assessment ID: {assessment.id}'
        )

        self.stdout.write(
            f'Status: {assessment.status}'
        )

        self.stdout.write(
            f'Overall band: {Decimal(score):.2f}'
        )

        self.stdout.write(
            f'Processing time: '
            f'{assessment.processing_time_ms or 0} ms'
        )

        self.stdout.write('')
        self.stdout.write('Feedback:')
        self.stdout.write(
            assessment.feedback or 'No feedback returned.'
        )

        self.stdout.write('')
        self.stdout.write('Strengths:')

        if assessment.strengths:
            for item in assessment.strengths:
                self.stdout.write(f'- {item}')
        else:
            self.stdout.write('- None provided.')

        self.stdout.write('')
        self.stdout.write('Weaknesses:')

        if assessment.weaknesses:
            for item in assessment.weaknesses:
                self.stdout.write(f'- {item}')
        else:
            self.stdout.write('- None provided.')

        self.stdout.write('')
        self.stdout.write('Suggestions:')

        if assessment.suggestions:
            for item in assessment.suggestions:
                self.stdout.write(f'- {item}')
        else:
            self.stdout.write('- None provided.')

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Result saved to AIAssessment #{assessment.id}.'
            )
        )
