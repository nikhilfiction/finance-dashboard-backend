from django.urls import path
from users.views import AdminUserListCreateView, AdminUserDetailView

urlpatterns = [
    path('', AdminUserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', AdminUserDetailView.as_view(), name='user-detail'),
]
