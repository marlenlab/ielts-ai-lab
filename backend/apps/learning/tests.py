from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import LearningActivity, LearningSession


User = get_user_model()


class LearningAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='learning_user',
            email='learning@example.com',
            password='StrongPassword123!',
        )

        self.other_user = User.objects.create_user(
            username='other_learning_user',
            email='other_learning@example.com',
            password='StrongPassword123!',
        )

        self.client.force_authenticate(user=self.user)

        self.session = LearningSession.objects.create(
            user=self.user,
            session_type=LearningSession.SessionType.MIXED,
            target_minutes=30,
        )

        self.activity = LearningActivity.objects.create(
            session=self.session,
            activity_type=LearningActivity.ActivityType.VOCABULARY,
            title='Vocabulary Practice',
            description='Learn and review vocabulary.',
            target_count=5,
            order=1,
        )

        self.second_activity = LearningActivity.objects.create(
            session=self.session,
            activity_type=LearningActivity.ActivityType.GRAMMAR,
            title='Grammar Practice',
            description='Practice grammar.',
            target_count=3,
            order=2,
        )

    def test_list_sessions(self):
        response = self.client.get(
            '/api/v1/learning/sessions/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['session_type'],
            'MIXED',
        )

    def test_create_session(self):
        response = self.client.post(
            '/api/v1/learning/sessions/',
            {
                'session_type': 'GRAMMAR',
                'target_minutes': 20,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            LearningSession.objects.filter(
                user=self.user,
            ).count(),
            2,
        )

    def test_session_detail_contains_activities(self):
        response = self.client.get(
            f'/api/v1/learning/sessions/{self.session.id}/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data['activities']),
            2,
        )

    def test_create_activity(self):
        response = self.client.post(
            f'/api/v1/learning/sessions/{self.session.id}/activities/',
            {
                'activity_type': 'READING',
                'title': 'Reading Practice',
                'description': 'Practice reading.',
                'target_count': 2,
                'order': 3,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self.session.activities.count(),
            3,
        )

    def test_duplicate_activity_order_is_rejected(self):
        response = self.client.post(
            f'/api/v1/learning/sessions/{self.session.id}/activities/',
            {
                'activity_type': 'READING',
                'title': 'Duplicate Order',
                'description': '',
                'target_count': 2,
                'order': 1,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_complete_activity_updates_progress(self):
        response = self.client.post(
            f'/api/v1/learning/activities/{self.activity.id}/complete/',
            {
                'completed_count': 2,
                'correct_count': 2,
                'incorrect_count': 0,
                'points_earned': 2,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.activity.refresh_from_db()

        self.assertEqual(
            self.activity.completed_count,
            2,
        )
        self.assertEqual(
            self.activity.correct_count,
            2,
        )
        self.assertEqual(
            self.activity.points_earned,
            2,
        )
        self.assertFalse(
            self.activity.is_completed(),
        )

    def test_complete_activity_marks_activity_completed(self):
        response = self.client.post(
            f'/api/v1/learning/activities/{self.activity.id}/complete/',
            {
                'completed_count': 5,
                'correct_count': 4,
                'incorrect_count': 1,
                'points_earned': 4,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.activity.refresh_from_db()

        self.assertEqual(
            self.activity.completed_count,
            5,
        )
        self.assertTrue(
            self.activity.is_completed(),
        )
        self.assertIsNotNone(
            self.activity.completed_at,
        )

    def test_session_progress(self):
        self.client.post(
            f'/api/v1/learning/activities/{self.activity.id}/complete/',
            {
                'completed_count': 3,
                'correct_count': 2,
                'incorrect_count': 1,
                'points_earned': 2,
            },
            format='json',
        )

        response = self.client.get(
            f'/api/v1/learning/sessions/{self.session.id}/progress/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        progress = response.data['progress']

        self.assertEqual(
            progress['total_activities'],
            2,
        )
        self.assertEqual(
            progress['total_target'],
            8,
        )
        self.assertEqual(
            progress['total_completed'],
            3,
        )
        self.assertEqual(
            progress['correct_answers'],
            2,
        )
        self.assertEqual(
            progress['incorrect_answers'],
            1,
        )
        self.assertEqual(
            progress['points_earned'],
            2,
        )
        self.assertEqual(
            progress['completion_percentage'],
            37.5,
        )
        self.assertEqual(
            progress['accuracy_percentage'],
            66.67,
        )

    def test_session_is_completed_when_all_activities_are_completed(self):
        first_response = self.client.post(
            f'/api/v1/learning/activities/{self.activity.id}/complete/',
            {
                'completed_count': 5,
                'correct_count': 5,
                'incorrect_count': 0,
                'points_earned': 5,
            },
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        self.session.refresh_from_db()

        self.assertEqual(
            self.session.status,
            LearningSession.Status.ACTIVE,
        )

        second_response = self.client.post(
            f'/api/v1/learning/activities/{self.second_activity.id}/complete/',
            {
                'completed_count': 3,
                'correct_count': 2,
                'incorrect_count': 1,
                'points_earned': 2,
            },
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.session.refresh_from_db()

        self.assertEqual(
            self.session.status,
            LearningSession.Status.COMPLETED,
        )
        self.assertIsNotNone(
            self.session.completed_at,
        )
        self.assertTrue(
            second_response.data['session_completed'],
        )

    def test_cancel_session(self):
        response = self.client.post(
            f'/api/v1/learning/sessions/{self.session.id}/cancel/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.session.refresh_from_db()

        self.assertEqual(
            self.session.status,
            LearningSession.Status.CANCELLED,
        )

    def test_cancel_completed_session_is_rejected(self):
        self.session.status = LearningSession.Status.COMPLETED
        self.session.save()

        response = self.client.post(
            f'/api/v1/learning/sessions/{self.session.id}/cancel/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_other_user_cannot_access_session(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            f'/api/v1/learning/sessions/{self.session.id}/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_other_user_cannot_access_activity(self):
        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            f'/api/v1/learning/activities/{self.activity.id}/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_negative_progress_is_rejected(self):
        response = self.client.post(
            f'/api/v1/learning/activities/{self.activity.id}/complete/',
            {
                'completed_count': -1,
                'correct_count': 0,
                'incorrect_count': 0,
                'points_earned': 0,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_activity_cannot_be_added_to_cancelled_session(self):
        self.session.status = LearningSession.Status.CANCELLED
        self.session.save()

        response = self.client.post(
            f'/api/v1/learning/sessions/{self.session.id}/activities/',
            {
                'activity_type': 'READING',
                'title': 'Reading Practice',
                'description': '',
                'target_count': 2,
                'order': 3,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_access_is_denied(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            '/api/v1/learning/sessions/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
