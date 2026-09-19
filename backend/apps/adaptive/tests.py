from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.grammar.models import (
    GrammarExercise,
    GrammarProgress,
    GrammarTopic,
)
from apps.learning.models import (
    LearningActivity,
    LearningSession,
)
from apps.vocabulary.models import (
    VocabularyProgress,
    VocabularyWord,
)

from .models import (
    AdaptiveProfile,
    AdaptiveRecommendation,
)
from .services import (
    calculate_skill_scores,
    complete_recommendation,
    create_adaptive_learning_session,
    generate_recommendations,
    get_adaptive_content,
    get_grammar_content,
    get_recommendation_priority,
    get_vocabulary_content,
    update_adaptive_profile,
)



User = get_user_model()


class AdaptiveServiceTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='adaptive_user',
            email='adaptive@example.com',
            password='testpass123',
        )

    def create_vocabulary_progress(
        self,
        word,
        mastery_score,
        correct_answers=1,
        incorrect_answers=0,
    ):
        return VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=mastery_score,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
        )

    def create_grammar_progress(
        self,
        topic,
        mastery_score,
        correct_answers=1,
        incorrect_answers=0,
    ):
        return GrammarProgress.objects.create(
            user=self.user,
            topic=topic,
            mastery_score=mastery_score,
            correct_answers=correct_answers,
            incorrect_answers=incorrect_answers,
        )

    def test_calculate_skill_scores_without_data(self):
        scores = calculate_skill_scores(self.user)

        self.assertIsNone(
            scores[AdaptiveProfile.Skill.VOCABULARY],
        )
        self.assertIsNone(
            scores[AdaptiveProfile.Skill.GRAMMAR],
        )

    def test_calculate_vocabulary_score(self):
        word_one = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources carefully.',
            difficulty='B2',
        )

        word_two = VocabularyWord.objects.create(
            word='assess',
            definition='to evaluate',
            example_sentence='We assess the situation.',
            difficulty='B2',
        )

        self.create_vocabulary_progress(
            word_one,
            Decimal('30.00'),
        )

        self.create_vocabulary_progress(
            word_two,
            Decimal('50.00'),
        )

        scores = calculate_skill_scores(self.user)

        self.assertEqual(
            scores[AdaptiveProfile.Skill.VOCABULARY],
            Decimal('40.00'),
        )

    def test_calculate_grammar_score(self):
        topic_one = GrammarTopic.objects.create(
            title='Present Perfect',
            description='Present perfect usage.',
            level='B1',
            explanation=(
                'Used for actions connected to the present.'
            ),
            examples=[],
            common_mistakes=[],
        )

        topic_two = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences.',
            level='B2',
            explanation=(
                'Used for hypothetical situations.'
            ),
            examples=[],
            common_mistakes=[],
        )

        self.create_grammar_progress(
            topic_one,
            Decimal('20.00'),
        )

        self.create_grammar_progress(
            topic_two,
            Decimal('60.00'),
        )

        scores = calculate_skill_scores(self.user)

        self.assertEqual(
            scores[AdaptiveProfile.Skill.GRAMMAR],
            Decimal('40.00'),
        )

    def test_update_adaptive_profile(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        self.create_vocabulary_progress(
            word,
            Decimal('30.00'),
        )

        profile = update_adaptive_profile(
            self.user,
        )

        self.assertEqual(
            profile.vocabulary_score,
            Decimal('30.00'),
        )

        self.assertEqual(
            profile.weakest_skill,
            AdaptiveProfile.Skill.VOCABULARY,
        )

        self.assertEqual(
            profile.strongest_skill,
            AdaptiveProfile.Skill.VOCABULARY,
        )

    def test_recommendation_priority(self):
        self.assertEqual(
            get_recommendation_priority(
                Decimal('20.00'),
            ),
            AdaptiveRecommendation.Priority.HIGH,
        )

        self.assertEqual(
            get_recommendation_priority(
                Decimal('50.00'),
            ),
            AdaptiveRecommendation.Priority.MEDIUM,
        )

        self.assertEqual(
            get_recommendation_priority(
                Decimal('80.00'),
            ),
            AdaptiveRecommendation.Priority.LOW,
        )

    def test_generate_recommendations(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        topic = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences.',
            level='B2',
            explanation='Conditional structures.',
            examples=[],
            common_mistakes=[],
        )

        self.create_vocabulary_progress(
            word,
            Decimal('30.00'),
        )

        self.create_grammar_progress(
            topic,
            Decimal('60.00'),
        )

        recommendations = generate_recommendations(
            self.user,
        )

        self.assertEqual(
            len(recommendations),
            2,
        )

        skills = {
            recommendation.skill
            for recommendation in recommendations
        }

        self.assertIn(
            AdaptiveProfile.Skill.VOCABULARY,
            skills,
        )

        self.assertIn(
            AdaptiveProfile.Skill.GRAMMAR,
            skills,
        )

    def test_generate_recommendations_replaces_old_uncompleted(
        self,
    ):
        old_recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Old recommendation',
                reason='Old reason',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('20.00'),
            )
        )

        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        self.create_vocabulary_progress(
            word,
            Decimal('30.00'),
        )

        recommendations = generate_recommendations(
            self.user,
        )

        self.assertEqual(
            len(recommendations),
            1,
        )

        self.assertFalse(
            AdaptiveRecommendation.objects.filter(
                pk=old_recommendation.pk,
            ).exists(),
        )

    def test_complete_recommendation(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Improve vocabulary',
                reason='Low vocabulary score.',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('20.00'),
            )
        )

        completed = complete_recommendation(
            recommendation,
        )

        self.assertTrue(
            completed.is_completed,
        )

        self.assertIsNotNone(
            completed.completed_at,
        )

    def test_complete_already_completed_recommendation(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Improve vocabulary',
                reason='Low vocabulary score.',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('20.00'),
                is_completed=True,
            )
        )

        original_completed_at = (
            recommendation.completed_at
        )

        completed = complete_recommendation(
            recommendation,
        )

        self.assertTrue(
            completed.is_completed,
        )

        self.assertEqual(
            completed.completed_at,
            original_completed_at,
        )


class AdaptiveAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='api_user',
            email='api@example.com',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def test_profile_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            reverse('adaptive-profile'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_profile_returns_user_profile(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=Decimal('30.00'),
            correct_answers=1,
            incorrect_answers=1,
        )

        response = self.client.get(
            reverse('adaptive-profile'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['weakest_skill'],
            AdaptiveProfile.Skill.VOCABULARY,
        )

        self.assertEqual(
            response.data['vocabulary_score'],
            '30.00',
        )

    def test_generate_recommendations_endpoint(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        topic = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences.',
            level='B2',
            explanation='Conditional structures.',
            examples=[],
            common_mistakes=[],
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=Decimal('30.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=topic,
            mastery_score=Decimal('60.00'),
        )

        response = self.client.post(
            reverse(
                'adaptive-recommendations-generate',
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['count'],
            2,
        )

    def test_recommendation_list_is_user_specific(self):
        AdaptiveRecommendation.objects.create(
            user=self.user,
            skill=AdaptiveProfile.Skill.VOCABULARY,
            title='My recommendation',
            reason='My reason',
            priority=AdaptiveRecommendation.Priority.HIGH,
            score=Decimal('20.00'),
        )

        AdaptiveRecommendation.objects.create(
            user=self.other_user,
            skill=AdaptiveProfile.Skill.GRAMMAR,
            title='Other recommendation',
            reason='Other reason',
            priority=AdaptiveRecommendation.Priority.HIGH,
            score=Decimal('20.00'),
        )

        response = self.client.get(
            reverse('adaptive-recommendations'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]['title'],
            'My recommendation',
        )

    def test_complete_recommendation_endpoint(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Improve vocabulary',
                reason='Low score.',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('20.00'),
            )
        )

        response = self.client.post(
            reverse(
                'adaptive-recommendation-complete',
                kwargs={
                    'pk': recommendation.pk,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data['is_completed'],
        )

    def test_cannot_complete_other_user_recommendation(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.other_user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Other recommendation',
                reason='Other reason.',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('20.00'),
            )
        )

        response = self.client.post(
            reverse(
                'adaptive-recommendation-complete',
                kwargs={
                    'pk': recommendation.pk,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AdaptiveLearningSessionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='session_user',
            email='session@example.com',
            password='testpass123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def test_create_adaptive_learning_session(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        topic = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences.',
            level='B2',
            explanation='Conditional structures.',
            examples=[],
            common_mistakes=[],
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=Decimal('30.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=topic,
            mastery_score=Decimal('60.00'),
        )

        response = self.client.post(
            reverse(
                'adaptive-learning-session',
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            len(response.data['activities']),
            2,
        )

        self.assertEqual(
            response.data['activities'][0][
                'target_count'
            ],
            15,
        )

        self.assertEqual(
            response.data['activities'][1][
                'target_count'
            ],
            10,
        )

        skills = {
            activity['content']['skill']
            for activity in response.data['activities']
        }

        self.assertEqual(
            skills,
            {
                AdaptiveProfile.Skill.VOCABULARY,
                AdaptiveProfile.Skill.GRAMMAR,
            },
        )

    def test_learning_session_contains_recommendation_ids(
        self,
    ):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=Decimal('30.00'),
        )

        session = create_adaptive_learning_session(
            self.user,
        )

        self.assertIsNotNone(
            session,
        )

        activity = session.activities.first()

        self.assertIsNotNone(
            activity,
        )

        self.assertIn(
            'recommendation_id',
            activity.content,
        )

        self.assertEqual(
            activity.content['skill'],
            AdaptiveProfile.Skill.VOCABULARY,
        )


class AdaptiveContentSelectionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='content_user',
            email='content@example.com',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            username='content_other',
            email='content_other@example.com',
            password='testpass123',
        )

    def test_vocabulary_content_prefers_low_mastery(self):
        weak_word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        strong_word = VocabularyWord.objects.create(
            word='excellent',
            definition='very good',
            example_sentence='She did an excellent job.',
            difficulty='B2',
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=weak_word,
            mastery_score=Decimal('20.00'),
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=strong_word,
            mastery_score=Decimal('90.00'),
        )

        content = get_vocabulary_content(
            user=self.user,
            target_count=1,
        )

        self.assertEqual(
            len(content),
            1,
        )

        self.assertEqual(
            content[0]['word'],
            'allocate',
        )

        self.assertEqual(
            content[0]['mastery_score'],
            20.0,
        )

    def test_vocabulary_content_contains_real_word_data(self):
        word = VocabularyWord.objects.create(
            word='assess',
            definition='to evaluate',
            example_sentence='We assess the situation.',
            translation='оценивать',
            difficulty='B2',
            topic='Business',
            part_of_speech='verb',
            pronunciation='əˈses',
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=Decimal('25.00'),
        )

        content = get_vocabulary_content(
            user=self.user,
            target_count=1,
        )

        self.assertEqual(
            content[0]['id'],
            word.id,
        )

        self.assertEqual(
            content[0]['word'],
            'assess',
        )

        self.assertEqual(
            content[0]['definition'],
            'to evaluate',
        )

        self.assertEqual(
            content[0]['translation'],
            'оценивать',
        )

        self.assertEqual(
            content[0]['topic'],
            'Business',
        )

    def test_vocabulary_content_is_user_specific(self):
        user_word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        other_word = VocabularyWord.objects.create(
            word='assess',
            definition='to evaluate',
            example_sentence='We assess the situation.',
            difficulty='B2',
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=user_word,
            mastery_score=Decimal('20.00'),
        )

        VocabularyProgress.objects.create(
            user=self.other_user,
            word=other_word,
            mastery_score=Decimal('10.00'),
        )

        content = get_vocabulary_content(
            user=self.user,
            target_count=10,
        )

        words = {
            item['word']
            for item in content
        }

        self.assertIn(
            'allocate',
            words,
        )

        self.assertNotIn(
            'assess',
            words,
        )

    def test_grammar_content_prefers_low_mastery_topic(self):
        weak_topic = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences.',
            level='B2',
            explanation='Conditional structures.',
            examples=[],
            common_mistakes=[],
        )

        strong_topic = GrammarTopic.objects.create(
            title='Articles',
            description='English articles.',
            level='B1',
            explanation='Articles usage.',
            examples=[],
            common_mistakes=[],
        )

        weak_exercise = GrammarExercise.objects.create(
            topic=weak_topic,
            exercise_type='MULTIPLE_CHOICE',
            question='If I ___ time, I would travel.',
            options=[
                'have',
                'had',
                'will have',
            ],
            correct_answer='had',
            explanation='Second conditional.',
            points=1,
            order=1,
        )

        GrammarExercise.objects.create(
            topic=strong_topic,
            exercise_type='MULTIPLE_CHOICE',
            question=(
                '___ apple a day keeps the doctor away.'
            ),
            options=[
                'A',
                'An',
                'The',
            ],
            correct_answer='An',
            explanation=(
                'Use an before a vowel sound.'
            ),
            points=1,
            order=1,
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=weak_topic,
            mastery_score=Decimal('20.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=strong_topic,
            mastery_score=Decimal('90.00'),
        )

        content = get_grammar_content(
            user=self.user,
            target_count=1,
        )

        self.assertEqual(
            len(content),
            1,
        )

        self.assertEqual(
            content[0]['id'],
            weak_exercise.id,
        )

        self.assertEqual(
            content[0]['topic_title'],
            'Conditionals',
        )

    def test_grammar_content_contains_real_exercise_data(self):
        topic = GrammarTopic.objects.create(
            title='Present Perfect',
            description='Present perfect.',
            level='B1',
            explanation=(
                'Actions connected to the present.'
            ),
            examples=[],
            common_mistakes=[],
        )

        exercise = GrammarExercise.objects.create(
            topic=topic,
            exercise_type='FILL_GAP',
            question='I have ___ my homework.',
            options=[],
            correct_answer='finished',
            explanation=(
                'Use the past participle.'
            ),
            points=1,
            order=1,
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=topic,
            mastery_score=Decimal('30.00'),
        )

        content = get_grammar_content(
            user=self.user,
            target_count=1,
        )

        self.assertEqual(
            content[0]['id'],
            exercise.id,
        )

        self.assertEqual(
            content[0]['question'],
            'I have ___ my homework.',
        )

        self.assertEqual(
            content[0]['exercise_type'],
            'FILL_GAP',
        )

    def test_adaptive_content_routes_by_skill(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute',
            example_sentence='We allocate resources.',
            difficulty='B2',
        )

        VocabularyProgress.objects.create(
            user=self.user,
            word=word,
            mastery_score=Decimal('20.00'),
        )

        content = get_adaptive_content(
            user=self.user,
            skill=AdaptiveProfile.Skill.VOCABULARY,
            target_count=1,
        )

        self.assertEqual(
            len(content),
            1,
        )

        self.assertEqual(
            content[0]['word'],
            'allocate',
        )


class AdaptiveActivityAnswerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='adaptive_answer_user',
            email='adaptive_answer@example.com',
            password='testpassword123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def create_vocabulary_activity(self):
        word = VocabularyWord.objects.create(
            word='allocate',
            definition='to distribute something',
            example_sentence=(
                'The manager decided to allocate '
                'more money to the project.'
            ),
            translation='распределять',
            difficulty='B2',
            topic='Business',
            part_of_speech='verb',
            pronunciation='/ˈæləkeɪt/',
        )

        recommendation = AdaptiveRecommendation.objects.create(
            user=self.user,
            skill=AdaptiveProfile.Skill.VOCABULARY,
            title='Improve vocabulary',
            reason='Vocabulary needs improvement.',
            priority=AdaptiveRecommendation.Priority.HIGH,
            score=25,
        )

        session = LearningSession.objects.create(
            user=self.user,
            session_type=LearningSession.SessionType.VOCABULARY,
            target_minutes=20,
        )

        activity = LearningActivity.objects.create(
            session=session,
            activity_type=LearningActivity.ActivityType.VOCABULARY,
            title='Vocabulary practice',
            description='Practice difficult vocabulary.',
            target_count=1,
            order=1,
            content={
                'skill': AdaptiveProfile.Skill.VOCABULARY,
                'items': [
                    {
                        'id': word.id,
                        'word': word.word,
                        'definition': word.definition,
                        'translation': word.translation,
                        'example_sentence': (
                            word.example_sentence
                        ),
                    },
                ],
            },
        )

        return (
            word,
            recommendation,
            session,
            activity,
        )

    def create_grammar_activity(self):
        topic = GrammarTopic.objects.create(
            title='Present Perfect',
            description=(
                'Using the present perfect tense.'
            ),
            level='B2',
            explanation=(
                'The present perfect connects '
                'past actions with the present.'
            ),
            examples=[
                'I have finished my work.',
            ],
            common_mistakes=[
                'Using the past simple incorrectly.',
            ],
        )

        exercise = GrammarExercise.objects.create(
            topic=topic,
            exercise_type='MULTIPLE_CHOICE',
            question=(
                'Choose the correct form: '
                'She ___ already finished.'
            ),
            options=[
                'has',
                'have',
                'had',
            ],
            correct_answer='has',
            explanation='She has finished.',
            points=2,
            order=1,
        )

        session = LearningSession.objects.create(
            user=self.user,
            session_type=LearningSession.SessionType.GRAMMAR,
            target_minutes=20,
        )

        activity = LearningActivity.objects.create(
            session=session,
            activity_type=LearningActivity.ActivityType.GRAMMAR,
            title='Grammar practice',
            description='Practice grammar.',
            target_count=1,
            order=1,
            content={
                'skill': AdaptiveProfile.Skill.GRAMMAR,
                'items': [
                    {
                        'id': exercise.id,
                        'question': exercise.question,
                        'options': exercise.options,
                        'correct_answer': (
                            exercise.correct_answer
                        ),
                        'explanation': (
                            exercise.explanation
                        ),
                        'points': exercise.points,
                    },
                ],
            },
        )

        return (
            topic,
            exercise,
            session,
            activity,
        )

    def test_vocabulary_correct_answer(
        self,
    ):
        (
            word,
            recommendation,
            session,
            activity,
        ) = self.create_vocabulary_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': word.id,
                'answer': 'allocate',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data['correct'],
        )

        activity.refresh_from_db()

        self.assertEqual(
            activity.completed_count,
            1,
        )

        self.assertEqual(
            activity.correct_count,
            1,
        )

        self.assertEqual(
            activity.incorrect_count,
            0,
        )

        progress = VocabularyProgress.objects.get(
            user=self.user,
            word=word,
        )

        self.assertEqual(
            progress.correct_answers,
            1,
        )

        self.assertEqual(
            progress.incorrect_answers,
            0,
        )

    def test_vocabulary_incorrect_answer(
        self,
    ):
        (
            word,
            recommendation,
            session,
            activity,
        ) = self.create_vocabulary_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': word.id,
                'answer': 'completely_wrong',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data['correct'],
        )

        activity.refresh_from_db()

        self.assertEqual(
            activity.completed_count,
            1,
        )

        self.assertEqual(
            activity.correct_count,
            0,
        )

        self.assertEqual(
            activity.incorrect_count,
            1,
        )

        progress = VocabularyProgress.objects.get(
            user=self.user,
            word=word,
        )

        self.assertEqual(
            progress.correct_answers,
            0,
        )

        self.assertEqual(
            progress.incorrect_answers,
            1,
        )

    def test_vocabulary_translation_answer(
        self,
    ):
        (
            word,
            recommendation,
            session,
            activity,
        ) = self.create_vocabulary_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': word.id,
                'answer': 'распределять',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data['correct'],
        )

    def test_grammar_correct_answer(
        self,
    ):
        (
            topic,
            exercise,
            session,
            activity,
        ) = self.create_grammar_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': exercise.id,
                'answer': 'has',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data['correct'],
        )

        activity.refresh_from_db()

        self.assertEqual(
            activity.completed_count,
            1,
        )

        self.assertEqual(
            activity.correct_count,
            1,
        )

        self.assertEqual(
            activity.points_earned,
            2,
        )

        progress = GrammarProgress.objects.get(
            user=self.user,
            topic=topic,
        )

        self.assertEqual(
            progress.correct_answers,
            1,
        )

        self.assertEqual(
            progress.incorrect_answers,
            0,
        )

    def test_grammar_incorrect_answer(
        self,
    ):
        (
            topic,
            exercise,
            session,
            activity,
        ) = self.create_grammar_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': exercise.id,
                'answer': 'have',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data['correct'],
        )

        activity.refresh_from_db()

        self.assertEqual(
            activity.completed_count,
            1,
        )

        self.assertEqual(
            activity.correct_count,
            0,
        )

        self.assertEqual(
            activity.incorrect_count,
            1,
        )

        self.assertEqual(
            activity.points_earned,
            0,
        )

        progress = GrammarProgress.objects.get(
            user=self.user,
            topic=topic,
        )

        self.assertEqual(
            progress.correct_answers,
            0,
        )

        self.assertEqual(
            progress.incorrect_answers,
            1,
        )

    def test_activity_belongs_to_another_user(
        self,
    ):
        (
            word,
            recommendation,
            session,
            activity,
        ) = self.create_vocabulary_activity()

        another_user = User.objects.create_user(
            username='another_adaptive_user',
            email='another_adaptive@example.com',
            password='testpassword123',
        )

        activity.session.user = another_user
        activity.session.save()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': word.id,
                'answer': 'allocate',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_item_id(
        self,
    ):
        (
            word,
            recommendation,
            session,
            activity,
        ) = self.create_vocabulary_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': 999999,
                'answer': 'allocate',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_empty_answer_rejected(
        self,
    ):
        (
            word,
            recommendation,
            session,
            activity,
        ) = self.create_vocabulary_activity()

        url = (
            f'/api/v1/adaptive/activities/'
            f'{activity.id}/answer/'
        )

        response = self.client.post(
            url,
            {
                'item_id': word.id,
                'answer': '',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
