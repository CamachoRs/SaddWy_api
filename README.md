**Vista de administrador:**

http://127.0.0.1:8000/admin/

<hr>

**Vista de documentación:**

- http://127.0.0.1:8000/api/v01/documentation/swagger/
- http://127.0.0.1:8000/api/v01/documentation/redoc/

<hr>

**Comandos para la instalación y ejecución del entorno:**

- python -m venv entorno
- .\entorno\Scripts\activate
- python -m pip install -r requirements.txt
- python manage.py runserver

<hr>

**Credenciales para ingresar a la vista de administrador:**

*correo:* prueba@gmail.com

*password:* prueba

<hr>

**Documentación del /refresh/**

Método = 'POST'

Respuestas = {
    200: 'Token renovado exitosamente',
    400: 'Token de actualización inválido o caducado'
}

Este endpoint permite a los usuarios renovar un token de acceso JWT caducado.
Se espera que los usuarios proporcionen un token de actualización válido para obtener un nuevo token de acceso.

parámetros:

    nombre: refresh

    en: body

    descripción: Token de actualización válido.

    requerido: true

    tipo: string

<hr>

Acordarse que *127.0.0.1:8000* puede variar dependiendo de su conexión, cuando ejecutan el comando *python manage.py runserver* les sale la dirección inicial. Con la dirección inicial de su computadora agregan lo adicional *(/admin/)* para completar la ruta. 