from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Dispatch
from .serializers import UserSerializer, LogInSerializer, DispatchSerializer


class SignUpView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class LogInView(TokenObtainPairView):
    serializer_class = LogInSerializer


class DispatchView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'id'
    lookup_url_kwarg = 'dispatch_id'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Dispatch.objects.all()
    serializer_class = DispatchSerializer
