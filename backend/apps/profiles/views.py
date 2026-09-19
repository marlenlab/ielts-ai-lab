from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions

from .models import LearnerProfile
from .serializers import LearnerProfileSerializer


class LearnerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = LearnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = LearnerProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile
    