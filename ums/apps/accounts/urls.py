from django.urls import path, re_path,include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    re_path(r'^group/type/$', GroupTypeListView.as_view()),
    re_path(r'^group/type/(?P<pk>[0-9a-f-]+)/$', GroupTypeDetailView.as_view()),
    re_path(r'^group/profile/$', GroupProfileListView.as_view()),
    path('',include(router.urls))
]
