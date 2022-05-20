from django.urls import path, re_path
from django.conf.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r'project', ProjectViewSet, basename='project')
router.register(r'achievement', AchievementViewSet, basename='achievement')
router.register(r'file', FileManagerViewSet, basename='file')
router.register(r'process', ProcessViewSet, basename='process')
router.register(r'task', TaskViewSet, basename='task')

urlpatterns = [path('', include(router.urls)),
               ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
