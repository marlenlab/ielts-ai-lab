from rest_framework import generics, permissions

from .serializers import LearnerAnalyticsSerializer
from .services import get_analytics


class AnalyticsDashboardView(generics.RetrieveAPIView):
    serializer_class = LearnerAnalyticsSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_object(self):
        return get_analytics(self.request.user)
