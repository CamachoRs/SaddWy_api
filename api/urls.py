from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg import views, openapi
from django.urls import path, include
from .views import *

schema_view = views.get_schema_view(
    openapi.Info(
        title = 'Documentación de la API de SaddWy',
        default_version = 'v01',
        description = 'API de SaddWy: Plataforma de aprendizaje en lógica de programación diseñada para ofrecer una experiencia educativa interactiva y accesible. Con un enfoque en el desarrollo lógico y algorítmico, SaddWy proporciona una amplia variedad de lecciones, ejercicios y desafíos diseñados para personas de todos los niveles de conocimiento en programación. Con una interfaz intuitiva y fácil de usar, nuestra API se esfuerza por mantener a los usuarios comprometidos y motivados en su viaje de aprendizaje',
        contact = openapi.Contact(email = 'saddwy2003@gmail.com'),
        license = openapi.License(name = 'Licencia propietaria')
    ), public = True
)
router = DefaultRouter()
router.register('users', UsuarioView)
router.register('languages', LenguajeView)
router.register('levels', NivelView)
router.register('questions', PreguntaView)
router.register('progress', ProgresoView)
router.register('photos', FotoView)
router.register('contact', Contactenos)

urlpatterns = [
    path('v01/register/', register),
    path('v01/validate/<str:token>/', validate),
    path('v01/login/', login),
    path('v01/start/', cards),
    path('v01/ranking/', ranking),
    path('v01/edit/', editUser),
    path('v01/questions/<int:id>/', questions),
    path('v01/profile/', profile),
    path('v01/contact/', ContactUs),
    path('v01/recovery/', recoveryEmail),
    path('v01/recover/<str:token>/', recoverAccount),
    path('v01/refresh/', TokenRefreshView.as_view()),
    path('v01/documentation/swagger/', schema_view.with_ui('swagger', cache_timeout = 0)),
    path('v01/documentation/redoc/', schema_view.with_ui('redoc', cache_timeout = 0)),
    path('v01/admin/', include(router.urls))
]