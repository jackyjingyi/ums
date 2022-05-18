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

urlpatterns = [
                  # re_path(r"$", ProjectCreateListView.as_view()),
                  # re_path(r"^instance/(?P<pk>[0-9a-f-]+)/$", ProjectDetailView.as_view()),
                  # re_path(r"^files/$", FileManagerListCreateView.as_view()),
                  re_path(r"^process/$", ProcessCreateListView.as_view()),
                  re_path(r"^process/(?P<pk>[0-9a-f-]+)/$", ProcessDetailView.as_view()),
                  re_path(r"^task/$", TaskListCreateView.as_view()),
                  re_path(r"^task/(?P<pk>[0-9a-f-]+)/$", TaskDetailView.as_view()),
                  path('', include(router.urls)),
                  # re_path(r"^project/achievement/$", )
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
