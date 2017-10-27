from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from user_app.views import index
from django.conf.urls.static import static

urlpatterns = [
	url(r'^$', index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^leave/', include('leave_application.urls', namespace='leave_application')),
    url(r'^profile/', include('user_app.urls', namespace='profile')),
	url(r'^calender/', include('calender.urls', namespace='calender')),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
