from smtplib import SMTPException
from .models import *
from .serializers import *
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core import validators, exceptions, mail
from django.db.models import Sum, Min
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, response, status, decorators, viewsets
from rest_framework_simplejwt import tokens, exceptions as TokenError
import difflib, re, jwt, imghdr, random, datetime, json

@swagger_auto_schema(
    method = 'POST',
    operation_summary = 'Registro de usuarios',
    responses = {
        201: 'Registro exitoso. Se envía un correo electrónico de confirmación.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description =
    """
    Este endpoint permite a los usuarios registrarse en el sistema proporcionando un nombre, correo electrónico y contraseña válidos.
    Se envía un correo electrónico de confirmación el cual tendrá validez durante 24 horas para completar el proceso de registro.

    ---
    parámetros
      - nombre: nombre
        en: body
        descripción: Nombre completo (entre 10 y 30 caracteres, sin números).
        requerido: true
        tipo: string

      - nombre: correo
        en: body
        descripción: Correo electrónico del usuario (máximo 254 caracteres, único en el sistema).
        requerido: true
        tipo: string

      - nombre: password
        en: body
        descripción: Contraseña del usuario (al menos 8 caracteres, al menos un carácter especial, al menos una letra mayúscula, al menos una letra minúscula, al menos un número, sin espacios y sin similitud con el nombre o correo).
        requerido: true
        tipo: string
    """
)
@decorators.api_view(['POST'])
def register(request):
    try:
        nombre = request.data['nombre']
        correo = request.data['correo']
        password = request.data['password']

        if len(nombre) < 10 or len(nombre) > 30:
            return http_400_bad_request('Por favor, ingrese un nombre válido con longitud de 10 a 30 caracteres')
        elif any(caracter.isdigit() for caracter in nombre):
            return http_400_bad_request('Por favor, evite incluir números en el nombre')

        if not correo:
            return http_400_bad_request('Por favor, asegúrate de ingresar tu correo electrónico. Este campo no puede estar vacío')
        elif len(correo) > 254:
            return http_400_bad_request('Por favor, ingrese un correo válido con un máximo de 254 caracteres')
        elif Usuario.objects.filter(correo = correo).exists():
            if Usuario.objects.filter(correo = correo, estado = True):
                return http_400_bad_request('Por favor selecciona otro correo electrónico, debido a que ya existe una cuenta asociada a este correo')
            elif Usuario.objects.filter(correo = correo, estado = False):
                Usuario.objects.filter(correo = correo, estado = False).delete()
        else:
            validators.validate_email(correo)

        if len(password) < 8:
            return http_400_bad_request('Por favor, ingresa una contraseña con un mínimo de 8 caracteres')
        elif ' ' in password:
            return http_400_bad_request('Por favor, asegúrate que tu contraseña no contenga espacios')
        elif not re.search(r'[A-Z]', password):
            return http_400_bad_request('Por favor, asegúrate de incluir al menos una letra mayúscula en tu contraseña')
        elif not re.search(r'[a-z]', password):
            return http_400_bad_request('Por favor, asegúrate de incluir al menos una letra minúscula en tu contraseña')
        elif not re.search(r'\d', password):
            return http_400_bad_request('Por favor, asegúrate de incluir al menos un número en tu contraseña')
        else:
            patron = r'[!@#$%^&*()\-_=+{};:,<.>/?[\]\'"`~\\|]'
            similitud_1 = difflib.SequenceMatcher(None, nombre.lower(), password.lower()).ratio()
            similitud_2 = difflib.SequenceMatcher(None, correo.lower(), password.lower()).ratio()
            if not re.search(patron, password):
                return http_400_bad_request('Por favor, asegúrate de incluir al menos un carácter especial en tu contraseña')
            elif similitud_1 > 0.5 and similitud_2 > 0.5:
                return http_400_bad_request('Por favor, elige una contraseña que no contenga información personal')
    
        request.data['password'] = make_password(password)
        if FotoPredeterminada.objects.count() > 0:
            idFoto = random.randint(1, FotoPredeterminada.objects.count())
            request.data['foto'] = FotoPredeterminada.objects.get(id = idFoto).foto

        serializer = UsuarioSerializer(data = request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            token = tokens.RefreshToken.for_user(usuario)
            mensaje = f"""
                Estimada/o {usuario.nombre},

                ¡Bienvenida/o a nuestro portal de programación! Estamos encantados de que te hayas registrado con nosotros.

                Para completar el proceso de registro y validar tu cuenta, por favor haz clic en el siguiente enlace:

                http://localhost:4200/login/{token}

                Este enlace te llevará a una página donde podrás confirmar tu dirección de correo electrónico y activar tu cuenta.

                Recuerda que si no has solicitado este registro, puedes ignorar este mensaje.

                Gracias por unirte a nosotros y esperamos que disfrutes de todas las funciones y recursos que nuestro portal tiene para ofrecer.

                Atentamente,
                SaddWy
            """
            mail.send_mail(
                '¡Bienvenido a SaddWy! Confirma tu cuenta para comenzar',
                mensaje,
                settings.EMAIL_HOST_USER,
                [usuario.correo],
                fail_silently = False,
            )
            return response.Response({
                'estado': 201,
                'validar': True,
                'mensaje': '¡Registro completado! Revisa tu bandeja de entrada para confirmar tu cuenta. No olvides verificar la carpeta de spam si no encuentras el correo en tu bandeja principal'
            }, status = status.HTTP_201_CREATED)
        else:
            return http_400_bad_request(serializer.errors)
    except KeyError:
        return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
    except exceptions.ValidationError:
            return http_400_bad_request('Por favor, verifica que el correo esté escrito correctamente debido a que has ingresado uno no válido')
    except FotoPredeterminada.DoesNotExist:
        return http_500_internal_server_error('Lo siento, no se pudo asignar una foto a tu perfil durante el registro. Por favor, inténtalo de nuevo')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'POST',
    operation_summary = 'Inicio de sesión de usuarios',
    responses = {
        200: 'Inicio de sesión exitoso. Se proporciona información del usuario y su progreso.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description =
    """
    Este endpoint permite a los usuarios iniciar sesión en el sistema proporcionando su correo electrónico y contraseña válidos.

    ---
    parámetros
      - nombre: correo
        en: body
        descripción: Correo electrónico del usuario.
        requerido: true
        tipo: string

      - nombre: password
        en: body
        descripción: Contraseña del usuario.
        requerido: true
        tipo: string
    """
)
@decorators.api_view(['POST'])
def login(request):
    try:
        correo = request.data['correo']
        password = request.data['password']

        if not correo:
            return http_400_bad_request('Por favor, asegúrate de ingresar tu correo electrónico. Este campo no puede estar vacío')
        if not password:
            return http_400_bad_request('Por favor, asegúrate de ingresar tu contraseña. Este campo no puede estar vacío')

        usuario = Usuario.objects.get(correo = correo)
        if not usuario.estado:
            return http_400_bad_request('¡Hola! Parece que aún no has validado tu cuenta. Por favor, verifica tu correo electrónico y sigue el enlace de validación para acceder a todas las funciones de nuestra plataforma')

        if not check_password(password, usuario.password):
            return http_400_bad_request('Lo siento, el correo y/o contraseña ingresados son incorrectos. Por favor, inténtalo nuevamente')

        usuarioSerializer = UsuarioSerializer(usuario)
        token = tokens.RefreshToken.for_user(usuario) 
        if not usuario.administrador:
            for lenguaje in Lenguaje.objects.filter(estado = True):
                if not Progreso.objects.filter(usuario = usuario, lenguaje = lenguaje).exists():
                    nivelesPermitidos = {nivel.nombre: (indice == 0) for indice, nivel in enumerate(Nivel.objects.filter(lenguaje = lenguaje))}
                    Progreso.objects.create(usuario = usuario, lenguaje = lenguaje, nivelesPermitidos = nivelesPermitidos)

        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Inicio de sesión exitoso!',
            'dato': {
                'foto': settings.BASE_URL + usuarioSerializer.data['foto'],
                'nombre': usuarioSerializer.data['nombre'],
                'acceso': str(token.access_token),
                'actualizar': str(token),
                'administrador': usuarioSerializer.data['administrador']
            }
        }, status = status.HTTP_200_OK)
    except KeyError:
        return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
    except Usuario.DoesNotExist:
        return http_400_bad_request('Lo siento, el correo y/o contraseña ingresados son incorrectos. Por favor, inténtalo nuevamente')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'GET',
    operation_summary = 'Validación de cuenta de usuario',
    responses = {
        200: 'Validación exitosa. La cuenta del usuario ha sido activada correctamente.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description = 'Este endpoint permite a los usuarios validar sus cuentas. Cuando un usuario se registra, se le envía un correo electrónico con un enlace único que lo redirige a esta vista. El enlace contiene un token encriptado que, al ser procesado por esta vista, activa la cuenta del usuario.'
)
@decorators.api_view(['GET'])
def validate(request, token):
    try:
        id = tokens.RefreshToken(token)
        usuario = Usuario.objects.get(id = id.payload['user_id'])
        if not usuario.estado:
            usuario.estado = True        
            usuario.save()            
            return response.Response({
                'estado': 200,
                'validar': True,
                'mensaje': '¡Bienvenido de nuevo a SaddWy! Estamos encantados de tenerte de regreso'
            }, status = status.HTTP_200_OK)
        else:
            return response.Response({
                'estado': 200,
                'validar': True,
                'mensaje': 'Su cuenta ya ha sido validada anteriormente. ¡Disfrute de su experiencia en SaddWy!'
            }, status = status.HTTP_200_OK)
    except (Usuario.DoesNotExist, TokenError.TokenError):
        return http_400_bad_request('Lo siento, pero el tiempo límite para activar su cuenta ha expirado. Por favor, regístrese nuevamente')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'POST',
    operation_summary = 'Solicitud de recuperación de contraseña',
    responses = {
        200: 'Solicitud de recuperación enviada exitosamente. Se proporciona un mensaje informativo.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description =
    """
    Este endpoint permite a los usuarios solicitar la recuperación de su contraseña. Se envía un correo electrónico con un enlace único para restablecer la contraseña.

    ---
    parámetros
      - nombre: correo
        en: body
        descripción: Correo electrónico asociado a la cuenta del usuario.
        requerido: true
        tipo: string
    """
)
@decorators.api_view(['POST'])
def recoveryEmail(request):
    try:
        correo = request.data['correo']
        
        if not correo:
            return http_400_bad_request('Por favor, asegúrate de ingresar tu correo electrónico. Este campo no puede estar vacío')
        elif len(correo) > 254:
            return http_400_bad_request('Por favor, ingrese un correo válido con un máximo de 254 caracteres')
        else:
            validators.validate_email(correo)
        
        usuario = Usuario.objects.get(correo = correo, estado = True)
        token = tokens.RefreshToken.for_user(usuario) 
        mensaje = f'''
            ¡Hola {usuario.nombre}!

            Hemos recibido una solicitud para restablecer tu contraseña en SaddWy. Si no realizaste esta solicitud, puedes ignorar este correo electrónico.

            Por favor, haz clic en el siguiente enlace para restablecer tu contraseña. Este enlace será válido por 24 horas, así que asegúrate de usarlo antes de que expire:

            http://localhost:4200/confirmarPassword/{token}/

            Si tienes algún problema, no dudes en ponerte en contacto con nuestro equipo de soporte.

            ¡Gracias!

            El equipo de SaddWy
            '''
        mail.send_mail(
            'Restablecimiento de contraseña en SaddWy',
            mensaje,
            settings.EMAIL_HOST_USER,
            [usuario.correo],
            fail_silently = False
        )
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Solicitud de recuperación de contraseña enviada! Hemos enviado un correo electrónico a la dirección proporcionada con un enlace para que puedas restablecer tu contraseña. Por favor, revisa tu bandeja de entrada dentro de las próximas 24 horas. Si no encuentras el correo en tu bandeja principal, asegúrate de verificar la carpeta de spam'
        })
    except KeyError:
        return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
    except exceptions.ValidationError:
        return http_400_bad_request('Por favor, verifica que el correo esté escrito correctamente debido a que has ingresado uno no válido')
    except Usuario.DoesNotExist:
        return http_400_bad_request('Lo siento, los datos ingresados son incorrectos. Por favor, inténtalo nuevamente')
    except SMTPException:
        return http_500_internal_server_error('Lo siento, ha habido un problema al enviar el correo electrónico. Por favor, intenta nuevamente más tarde')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'POST',
    operation_summary = 'Recuperación de cuenta de usuario',
    responses = {
        200: 'Recuperación exitosa. La contraseña de la cuenta del usuario ha sido actualizada correctamente.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
    """
    Este endpoint permite a los usuarios recuperar su cuenta después de recibir un enlace con un token encriptado. 
    Una vez redirigidos aquí desde el enlace, se solicita al usuario ingresar una nueva contraseña.

    ---
    parámetros
      - nombre: password
        en: body
        descripción: Nueva contraseña para la cuenta del usuario (al menos 8 caracteres, al menos un carácter especial, al menos una letra mayúscula, al menos una letra minúscula, al menos un número, sin espacios y sin similitud con el nombre o correo).
        requerido: true
        tipo: string
    """
)
@decorators.api_view(['POST'])
def recoverAccount(request, token):
    try:
        id = tokens.RefreshToken(token)
        password = request.data['password']
        usuario = Usuario.objects.get(id = id.payload['user_id'], estado = True)
        
        if len(password) < 8:
            return http_400_bad_request('Por favor, ingresa una contraseña con un mínimo de 8 caracteres')
        elif ' ' in password:
            return http_400_bad_request('Por favor, asegúrate que tu contraseña no contenga espacios')
        elif not re.search(r'[A-Z]', password):
            return http_400_bad_request('Por favor, asegúrate de incluir al menos una letra mayúscula en tu contraseña')
        elif not re.search(r'[a-z]', password):
            return http_400_bad_request('Por favor, asegúrate de incluir al menos una letra minúscula en tu contraseña')
        elif not re.search(r'\d', password):
            return http_400_bad_request('Por favor, asegúrate de incluir al menos un número en tu contraseña')
        else:
            patron = r'[!@#$%^&*()\-_=+{};:,<.>/?[\]\'"`~\\|]'
            similitud1 = difflib.SequenceMatcher(None, usuario.nombre.lower(), password.lower()).ratio()
            similitud2 = difflib.SequenceMatcher(None, usuario.correo.lower(), password.lower()).ratio()
            if not re.search(patron, password):
                return http_400_bad_request('Por favor, asegúrate de incluir al menos un carácter especial en tu contraseña')
            elif similitud1 > 0.5 and similitud2 > 0.5:
                return http_400_bad_request('Por favor, elige una contraseña que no contenga información personal')
        
        usuario.password = make_password(password)
        usuario.save()
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Contraseña actualizada correctamente!'
        }, status = status.HTTP_200_OK)
    except KeyError:
        return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
    except (Usuario.DoesNotExist, TokenError.TokenError):
        return http_400_bad_request('Lo siento, pero el tiempo límite para recuperar su cuenta ha expirado. Por favor, solicite un nuevo correo')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'GET',
    operation_summary = 'Perfil de usuario',
    responses = {
        200: 'Perfil del usuario obtenido exitosamente.',
        400: 'Error en la solicitud. Puede ocurrir si el token de acceso proporcionado es inválido o tiene un formato incorrecto.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
    """
    Este endpoint permite a un usuario autenticado obtener información detallada de su perfil, incluyendo su información personal y su progreso en la aplicación.

    ---
    parámetros
    - nombre: Authorization
        en: header
        descripción: Token de autenticación del usuario.
        requerido: true
        tipo: string
        format: JWT
    """
)
@decorators.api_view(['GET'])
@decorators.permission_classes([permissions.IsAuthenticated])
def profile(request):
    try:
        token = request.headers.get('Authorization').split()[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms = ["HS256"])
        usuario = Usuario.objects.get(id = payload['user_id'])
        usuarioSerializer = UsuarioSerializer(usuario)
        progresoSerializer = ProgresoSerializer(Progreso.objects.filter(usuario = usuario.id), many = True)
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '',
            'dato': {
                'usuario': {
                    'foto': settings.BASE_URL + usuarioSerializer.data['foto'],
                    'nombre': usuarioSerializer.data['nombre'],
                    'correo': usuarioSerializer.data['correo'],
                    'racha': usuarioSerializer.data['racha'],
                    'registro': usuarioSerializer.data['registro']
                },
                'progreso': progresoSerializer.data
            }
        }, status = status.HTTP_200_OK)
    except (IndexError, jwt.exceptions.InvalidTokenError):
        return http_400_bad_request('El token de acceso que has proporcionado no es válido o tiene un formato incorrecto. Por favor, revisa y asegúrate de que el token sea correcto')
    except (jwt.exceptions.DecodeError, Usuario.DoesNotExist, Progreso.DoesNotExist):
        return http_500_internal_server_error('Lo siento, ha ocurrido un problema al procesar tu solicitud. Por favor, intenta nuevamente más tarde')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'GET',
    operation_summary = 'Obtener tarjetas de lenguajes',
    responses = {
        200: 'Éxito. Se devuelven las tarjetas de los lenguajes disponibles.',
        401: 'No autorizado. El usuario no tiene permiso para acceder a esta función.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
    """
    Este endpoint permite a los usuarios autorizados visualizar las tarjetas de los lenguajes disponibles, junto con sus niveles respectivos. Los niveles que están marcados como activos están permitidos para que el usuario pueda comenzar las actividades y desbloquear más niveles.

    ---
    parámetros
    - nombre: Authorization
        en: header
        descripción: Token de autenticación del usuario.
        requerido: true
        tipo: string
        format: JWT
    """
)
@decorators.api_view(['GET'])
@decorators.permission_classes([permissions.IsAuthenticated])
def cards(request):
    try:    
        serializer = CartaSerializer(Lenguaje.objects.filter(estado = True), many = True, context = {'request': request})
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Excelente! La información ha sido procesada exitosamente',
            'dato': serializer.data
        }, status = status.HTTP_200_OK)
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'GET',
    operation_summary = 'Explorar ranking de usuarios',
    responses = {
        200: 'Éxito. Se devuelve el ranking de usuarios y la posición del usuario autenticado.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
    """
    Este endpoint permite a los usuarios autenticados explorar el ranking de usuarios y comparar sus puntos con otros participantes en la plataforma. Además de proporcionar una visión general del ranking, también muestra la posición actual del usuario autenticado.
    
    ---
    parámetros
    - nombre: Authorization
        en: header
        descripción: Token de autenticación del usuario.
        requerido: true
        tipo: string
        format: JWT
    """
)
@decorators.api_view(['GET'])
@decorators.permission_classes([permissions.IsAuthenticated])
def ranking(request):
    try:
        token = request.headers.get('Authorization').split()[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms = ["HS256"])
        progresos = Progreso.objects.values('usuario').annotate(
            puntos = Sum('puntos'), 
            registro = Min('registro')
        ).order_by('-puntos', 'registro')[:50]
        listado = {}
        for i, resultado in enumerate(progresos, start = 1):
            listado[i] = {
                'puesto': i,
                'nombre': Usuario.objects.get(id = resultado['usuario']).nombre,
                'puntos': resultado['puntos']
            }
            if resultado['usuario'] == payload['user_id']:
                usuario = {
                    'puesto': i,
                    'nombre': Usuario.objects.get(id = payload['user_id']).nombre,
                    'puntos': resultado['puntos']
                }
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Explora el ranking de los usuarios y compara tus puntos!',
            'dato': {
                'listado': listado,
                'usuario': usuario
            }
        }, status = status.HTTP_200_OK)
    except (IndexError, jwt.exceptions.InvalidTokenError):
        return http_400_bad_request('El token de acceso que has proporcionado no es válido o tiene un formato incorrecto. Por favor, revisa y asegúrate de que el token sea correcto')
    except (jwt.exceptions.DecodeError, Usuario.DoesNotExist):
        return http_500_internal_server_error('Lo siento, ha ocurrido un problema al procesar tu solicitud. Por favor, intenta nuevamente más tarde')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'PUT',
    operation_summary = 'Editar información del usuario',
    responses = {
        200: 'Éxito. La información del usuario ha sido actualizada correctamente.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
    """
    Este endpoint permite a los usuarios autenticados editar su información personal, incluyendo la foto de perfil, nombre y contraseña.

    ---
    parámetros
    - nombre: Authorization
        en: header
        descripción: Token de autenticación del usuario.
        requerido: true
        tipo: string
        format: JWT

    - nombre: foto
        en: body
        descripción: Nueva foto de perfil del usuario en formato base64 (solo se permiten formatos JPG o PNG).
        requerido: false
        tipo: string

    - nombre: nombre
        en: body
        descripción: Nuevo nombre (entre 10 y 30 caracteres, sin números).
        requerido: false
        tipo: string

    - nombre: password
        en: body
        descripción: Contraseña del usuario (al menos 8 caracteres, al menos un carácter especial, al menos una letra mayúscula, al menos una letra minúscula, al menos un número, sin espacios y sin similitud con el nombre o correo).
        requerido: false
        tipo: string
    """
)
@decorators.api_view(['PUT'])
@decorators.permission_classes([permissions.IsAuthenticated])
def editUser(request):
    try:
        token = request.headers.get('Authorization').split()[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms = ["HS256"])
        usuario = Usuario.objects.get(id = payload['user_id'])
        foto = request.FILES.get('foto')
        nombre = request.data.get('nombre')
        password = request.data.get('password')
        datos = request.data.copy()

        if foto:
            if not foto.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                return http_400_bad_request('Por favor, asegúrate de cargar una imagen en formato JPG o PNG para completar el proceso')
            if 'predeterminado' not in usuario.foto.path:
                usuario.foto.delete()

        if nombre:
            if len(nombre) < 10 or len(nombre) > 30:
                return http_400_bad_request('Por favor, ingrese un nombre válido con longitud de 10 a 30 caracteres')
            elif any(caracter.isdigit() for caracter in nombre):
                return http_400_bad_request('Por favor, evite incluir números en el nombre')
        else:
            nombre = usuario.nombre
            
        if password:
            if len(password) < 8:
                return http_400_bad_request('Por favor, ingresa una contraseña con un mínimo de 8 caracteres')
            elif ' ' in password:
                return http_400_bad_request('Por favor, asegúrate que tu contraseña no contenga espacios')
            elif not re.search(r'[A-Z]', password):
                return http_400_bad_request('Por favor, asegúrate de incluir al menos una letra mayúscula en tu contraseña')
            elif not re.search(r'[a-z]', password):
                return http_400_bad_request('Por favor, asegúrate de incluir al menos una letra minúscula en tu contraseña')
            elif not re.search(r'\d', password):
                return http_400_bad_request('Por favor, asegúrate de incluir al menos un número en tu contraseña')
            else:
                patron = r'[!@#$%^&*()\-_=+{};:,<.>/?[\]\'"`~\\|]'
                similitud_1 = difflib.SequenceMatcher(None, nombre.lower(), password.lower()).ratio()
                similitud_2 = difflib.SequenceMatcher(None, usuario.correo.lower(), password.lower()).ratio()
                if not re.search(patron, password):
                    return http_400_bad_request('Por favor, asegúrate de incluir al menos un carácter especial en tu contraseña')
                elif similitud_1 > 0.5 and similitud_2 > 0.5:
                    return http_400_bad_request('Por favor, elige una contraseña que no contenga información personal')
            datos['password'] = make_password(password)

        usuarioSerializer = UsuarioSerializer(instance = usuario, data = datos, partial = True)
        if usuarioSerializer.is_valid():
            usuarioSerializer.save()
            return response.Response({
                'estado': 200,
                'validar': True,
                'mensaje': '¡Información actualizada exitosamente!',
                'dato': {
                    'foto': settings.BASE_URL + usuarioSerializer.data['foto'],
                    'nombre': usuarioSerializer.data['nombre'],
                    'correo': usuarioSerializer.data['correo'],
                }
            }, status = status.HTTP_200_OK)
        else:
            return http_400_bad_request(usuarioSerializer.errors)
    except (IndexError, jwt.exceptions.InvalidTokenError):
        return http_400_bad_request('El token de acceso que has proporcionado no es válido o tiene un formato incorrecto. Por favor, revisa y asegúrate de que el token sea correcto')
    except (jwt.exceptions.DecodeError, Usuario.DoesNotExist):
        return http_500_internal_server_error('Lo siento, ha ocurrido un problema al procesar tu solicitud. Por favor, intenta nuevamente más tarde')
    except Exception as e:
        return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'GET',
    operation_summary = 'Obtener preguntas por id',
    responses = {
        200: 'Éxito. Devuelve las preguntas del nivel especificado.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        401: 'No autorizado. El usuario no tiene permiso para acceder a este recurso.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
        """
    Este endpoint permite a los usuarios autenticados obtener una pregunta específica mediante su ID.
    
    ---
    parámetros:
    - nombre: id
      en: path
      descripción: ID de la pregunta que se desea obtener.
      requerido: true
      tipo: integer

    - nombre: Authorization
      en: header
      descripción: Token de autenticación del usuario.
      requerido: true
      tipo: string
      format: JWT
    """
)
@swagger_auto_schema(
    method = 'POST',
    operation_summary = 'Actualizar progreso y estado del usuario',
    responses = {
        200: 'Éxito. Devuelve información actualizada del usuario y su progreso.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        401: 'No autorizado. El token de acceso proporcionado es inválido o está en un formato incorrecto.',
        500: 'Error interno del servidor.'
    },
    operation_description = 
    """
    Este endpoint permite a los usuarios autenticados actualizar su progreso y estado al completar preguntas en un nivel específico.

    ---
    parámetros:
    - nombre: id
      en: path
      descripción: ID de la pregunta que se ha completado.
      requerido: true
      tipo: integer

    - nombre: Authorization
      en: header
      descripción: Token de autenticación del usuario.
      requerido: true
      tipo: string
      format: JWT
      
    - nombre: intentos
      en: body
      descripción: El número de intentos realizados para completar las preguntas.
      requerido: true
      tipo: string
    """
)
@decorators.api_view(['GET', 'POST'])
@decorators.permission_classes([permissions.IsAuthenticated])
def questions(request, id):
    if request.method == 'GET':
        try:
            niveles = Nivel.objects.get(id = id, estado = True)
            serializer = PreguntaSerializer(Pregunta.objects.filter(nivel = niveles, estado = True), many = True)
            return response.Response({
                'estado': 200,
                'validar': True,
                'mensaje': '¡Vamos para aprender! Prepárate para sumergirte mientras avanzamos juntos. ¡Veamos qué descubrimos!',
                'dato': serializer.data
            }, status = status.HTTP_200_OK)
        except KeyError:
            return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
        except Nivel.DoesNotExist:
            return http_400_bad_request('El nivel especificado no existe o no está disponible en este momento.')
        except Exception as e:
            return http_500_internal_server_error(str(e))
    elif request.method == 'POST':
        try:
            token = request.headers.get('Authorization').split()[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms = ["HS256"])
            usuario = Usuario.objects.get(id = payload['user_id'])
            intentos = request.data['intentos']
            nivel = Nivel.objects.get(id = id, estado = True)
            nombreNivel = nivel.nombre
            progreso = Progreso.objects.get(usuario = usuario, lenguaje = nivel.lenguaje)
            dias = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes',
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            nombreDia = dias.get(datetime.datetime.now().strftime("%A"))
            usuario.racha[nombreDia] = True
            usuario.save()
            nivelesPermitidos = progreso.nivelesPermitidos
            if nombreNivel in nivelesPermitidos:
                listaNiveles = list(nivelesPermitidos.keys())
                posicion = listaNiveles.index(nombreNivel)
                if posicion + 1 < len(listaNiveles):
                    siguienteNivel = listaNiveles[posicion + 1]
                    if not nivelesPermitidos[siguienteNivel]:
                        if nivel.totalPreguntas <= intentos:
                            progreso.puntos += nivel.totalPreguntas
                        else:
                            progreso.puntos += (nivel.totalPreguntas - intentos) * 2 + nivel.totalPreguntas
                        
                        nivelesPermitidos[siguienteNivel] = True
                    else:
                        return response.Response({
                            'estado': 200,
                            'validar': True,
                            'mensaje': f'¡Felicitaciones! Ya has completado el nivel {siguienteNivel} anteriormente'
                        })
                
                if posicion == len(listaNiveles):
                    if nivel.totalPreguntas <= intentos:
                        progreso.puntos += nivel.totalPreguntas
                    else:
                        progreso.puntos += (nivel.totalPreguntas - intentos) * 2 + nivel.totalPreguntas
                    
            num_nivelesPermitidos = sum(valor for valor in progreso.nivelesPermitidos.values() if valor)
            progreso.progresoLenguaje = (num_nivelesPermitidos - 1)*100 / nivel.totalPreguntas
            progreso.save()
            return response.Response({
                'estado': 200,
                'validar': True,
                'mensaje': '¡Fantástico! ¡Has completado todas las preguntas!. ¡Sigue así y estarás dominando la programación en poco tiempo!'
            })
        except KeyError:
            return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
        except (IndexError, jwt.exceptions.InvalidTokenError, json.JSONDecodeError):
            return http_400_bad_request('El token de acceso que has proporcionado no es válido o tiene un formato incorrecto. Por favor, revisa y asegúrate de que el token sea correcto')
        except Nivel.DoesNotExist:
            return http_400_bad_request('Lo siento, el nivel especificado no existe en el sistema. Por favor, verifica el nombre del nivel e inténtalo nuevamente')
        except jwt.exceptions.DecodeError:
            return http_500_internal_server_error('Lo siento, ha ocurrido un problema al procesar tu solicitud. Por favor, intenta nuevamente más tarde')
        except Progreso.DoesNotExist:
            return http_500_internal_server_error('Lo siento, no hemos podido encontrar el progreso asignado automáticamente para este usuario. Por favor, comunícate con el equipo de soporte para obtener asistencia')
        except ValueError:
            return http_500_internal_server_error('Lo siento, no pudimos completar la operación de conversión de datos debido a un error interno del sistema. Por favor, comunícate con el equipo técnico para obtener asistencia')
        except Exception as e:
            return http_500_internal_server_error(str(e))

@swagger_auto_schema(
    method = 'POST',
    operation_summary = 'Registro de usuarios',
    responses = {
        200: 'Éxito. El mensaje ha sido enviado correctamente.',
        400: 'Error en la solicitud. Se proporciona un mensaje descriptivo del error.',
        401: 'No autorizado. El usuario no tiene permiso para acceder a este recurso.',
        500: 'Error interno del servidor.'
    },
    operation_description =
    """
    Este endpoint permite a los usuarios enviar mensajes de contacto al sistema. Se requiere que el usuario esté autenticado para realizar esta acción.

    ---
    parámetros:
      - nombre: nombre
        en: body
        descripción: Nombre completo del remitente (entre 10 y 30 caracteres, sin números)
        requerido: true
        tipo: string

      - nombre: celular
        en: body
        descripción: Número de celular del remitente (debe tener formato Colombiano, iniciando con 3 y teniendo 10 dígitos de longitud)
        requerido: true
        tipo: string

      - nombre: correo
        en: body
        descripción: Correo electrónico del remitente (que sea un correo valido)
        requerido: true
        tipo: string

      - nombre: mensaje
        en: body
        descripción: Mensaje del remitente (entre 15 y 255 caracteres)
        requerido: true
        tipo: string
    """
)
@decorators.api_view(['POST'])
@decorators.permission_classes([permissions.IsAuthenticated])
def ContactUs(request):
    try:
        nombre = request.data['nombre']
        celular = request.data['celular']
        correo = request.data['correo']
        mensaje = request.data['mensaje']

        if len(nombre) < 10 or len(nombre) > 30:
            return http_400_bad_request('Por favor, ingrese un nombre válido con longitud de 10 a 30 caracteres')
        elif any(caracter.isdigit() for caracter in nombre):
            return http_400_bad_request('Por favor, evite incluir números en el nombre')
        
        if celular[0] != '3' or len(celular) != 10:
            return http_400_bad_request('El número de celular proporcionado no es válido para Colombia. Por favor, verifica e inténtalo nuevamente.')

        if not correo:
            return http_400_bad_request('Por favor, asegúrate de ingresar tu correo electrónico. Este campo no puede estar vacío')
        elif len(correo) > 254:
            return http_400_bad_request('Por favor, ingrese un correo válido con un máximo de 254 caracteres')
        else:
            validators.validate_email(correo)
        
        if len(mensaje) < 15:
            return http_400_bad_request('Por favor, ingrese un mensaje válido con un mínimo de 15 caracteres')
        elif len(mensaje) > 255:
            return http_400_bad_request('Por favor, ingrese un mensaje válido con un máximo de 255 caracteres')
        
        serializer = ContactarSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return response.Response({
                'estado': 200,
                'validar': True,
                'mensaje': '¡Gracias por ponerte en contacto con nosotros! Tu mensaje ha sido enviado correctamente y nos pondremos en contacto contigo lo antes posible'
            }, status = status.HTTP_201_CREATED)
        else:
            return http_400_bad_request(serializer.errors)
    except KeyError:
        return http_400_bad_request('Por favor, proporciona los datos obligatorios que faltan en la solicitud')
    except exceptions.ValidationError:
            return http_400_bad_request('Por favor, verifica que el correo esté escrito correctamente debido a que has ingresado uno no válido')
    except exceptions.PermissionDenied:
        return http_400_bad_request('No tienes permisos para realizar esta acción')
    except Exception as e:
        return http_500_internal_server_error(str(e))

def http_400_bad_request(mensaje):
    return response.Response({
        'estado': 400,
        'validar': False,
        'mensaje': mensaje
    }, status = status.HTTP_400_BAD_REQUEST)

def http_404_not_found():
    return response.Response({
        'estado': 404,
        'validar': False,
        'mensaje': 'Lo siento, la dirección URL ingresada no es válida. Te sugiero verificarla y volver a intentarlo'
    }, status = status.HTTP_404_NOT_FOUND)

def http_500_internal_server_error(mensaje):
    return response.Response({
        'estado': 500,
        'validar': False,
        'mensaje': mensaje
    }, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

class UsuarioView(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializerAdmin
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data = request.data, partial = True)
        serializer.is_valid(raise_exception = True)
        self.perform_update(serializer)
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Información actualizada exitosamente!',
            'dato': serializer.data
        }, status = status.HTTP_200_OK)

class LenguajeView(viewsets.ModelViewSet):
    queryset = Lenguaje.objects.all()
    serializer_class = LenguajeSerializerAdmin
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data = request.data, partial = True)
        serializer.is_valid(raise_exception = True)
        self.perform_update(serializer)
        return response.Response({
            'estado': 200,
            'validar': True,
            'mensaje': '¡Información actualizada exitosamente!',
            'dato': serializer.data
        }, status = status.HTTP_200_OK)

class NivelView(viewsets.ModelViewSet):
    queryset = Nivel.objects.all()
    serializer_class = NivelSerializerAdmin
    permission_classes = [permissions.IsAuthenticated]

class PreguntaView(viewsets.ModelViewSet):
    queryset = Pregunta.objects.all()
    serializer_class = PreguntaSerializerAdmin
    permission_classes = [permissions.IsAuthenticated]

class ProgresoView(viewsets.ModelViewSet):
    queryset = Progreso.objects.all()
    serializer_class = ProgresoSerializerAdmin
    permission_classes = [permissions.IsAuthenticated]

class FotoView(viewsets.ModelViewSet):
    queryset = FotoPredeterminada.objects.all()
    serializer_class = FotoSerializerAdmin
    permission_classes = [permissions.IsAuthenticated]

class Contactenos(viewsets.ModelViewSet):
    queryset = Contactar.objects.all()
    serializer_class = ContactarSerializer
    permission_classes = [permissions.IsAuthenticated]