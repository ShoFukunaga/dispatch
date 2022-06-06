from django.urls import path

from .views import DispatchView

app_name = 'core'

urlpatterns = [
    path('', DispatchView.as_view({'get': 'list'}), name='dispatch_list'),
    path('<uuid:dispatch_id>/', DispatchView.as_view({'get': 'retrieve'}), name='dispatch_detail'),  # new
]
