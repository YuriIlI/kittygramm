from rest_framework import routers

from django.contrib import admin
from django.urls import include, path

from cats.views import AchievementViewSet, CatViewSet, UserViewSet


router = routers.DefaultRouter()
router.register('cats', CatViewSet)
router.register('users', UserViewSet)
router.register('achievements', AchievementViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

# kittygram2/urls.py
from cats.views import AdoptionApplicationViewSet

router.register(r'applications', AdoptionApplicationViewSet, basename='application')