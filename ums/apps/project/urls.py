from django.urls import path, re_path
from django.conf.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings

from .views import *

urlpatterns = [
                  re_path(r"$", ProjectCreateListView.as_view()),
                  re_path(r"^instance/(?P<pk>[0-9a-f-]+)/$", ProjectDetailView.as_view()),
                  re_path(r"^process/$", ProcessCreateListView.as_view()),
                  re_path(r"^process/(?P<pk>[0-9a-f-]+)/$", ProcessDetailView.as_view()),
                  # re_path(r"^project/achievement/$", )
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
