# Mesa Viva — Actividad 5

Página de recetas para **Desarrollo Web Profesional, Segundo Parcial, Unidad 3**.

Autor: Carlos Manuel Vallejo Puente · IDGS 9-3  
Docente: José Julián Reyes Patiño

## Ejecutar en esta computadora

El entorno virtual, las dependencias, el archivo `.env` y la base de datos ya están preparados.

1. Abre esta carpeta en el explorador.
2. Haz doble clic en **`iniciar.bat`** y deja abierta la ventana.
3. Visita **http://127.0.0.1:8000/**.
4. Para detener la página, presiona `Ctrl+C` en la ventana del servidor.

Si el puerto 8000 está ocupado, ejecuta `.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001` y abre el puerto 8001. No hay cuentas de demostración ni contraseñas predefinidas: registra tu propia cuenta con datos de prueba.

## Tema y pantallas

**Mesa Viva** invita a descubrir platos del mundo y guardarlos en un recetario personal.

| Pantalla | Ruta | Función |
|---|---|---|
| Inicio | `/` | Presentación, categorías sugeridas y accesos |
| Registro | `/registro/` | Nombre, correo, contraseña, confirmación y aceptación del aviso |
| Ingreso | `/ingresar/` | Inicio de sesión por correo |
| Explorar recetas | `/recetas/` | Buscar recetas en una API real |
| Detalle | `/recetas/52771/` | Ingredientes marcables, instrucciones y video cuando existe |
| Mis favoritos | `/favoritos/` | Recetas guardadas, exclusivas de cada cuenta |
| Privacidad | `/privacidad/` | Uso de datos y alcance académico |

La interfaz es responsive, tiene navegación con teclado, etiquetas en formularios, estados de carga, mensajes sin resultados y opción de reintento ante fallas de conexión.

## Relación con las prácticas anteriores

Se revisaron las prácticas dentro de la carpeta de la materia:

- **Primer Parcial / Actividad 3 / django-project:** organización por proyecto y aplicación Django, modelos, servicios separados, serializers, permisos y Django REST Framework. Mesa Viva mantiene esa separación en `config/` y `recipes/`.
- **Segundo Parcial / Actividades 1 a 3:** control de versiones y exclusión de archivos locales con `.gitignore`. La Actividad 3 contiene una introducción a React/Vite; aquí se usa Django con plantillas y JavaScript para reunir interfaz, base de datos y servidor en un solo proyecto que se inicia con un comando.
- **Segundo Parcial / Actividad 4:** validación en servidor, hash de contraseñas, protección de secretos, sesiones, autorización por recurso, servicios REST y API externa.

Se usa **SQLite** para que la entrega funcione sin instalar ni configurar MySQL. No es una copia del proyecto de productos; es una aplicación nueva construida con los conceptos de las prácticas.

## Requisitos de la actividad

| Requisito | Implementación |
|---|---|
| Inicio | Portada con tema propio |
| Registro validado | Validación HTML/JavaScript y validación definitiva en Django |
| Información del tema | Buscador y detalle de recetas reales |
| API externa gratuita | TheMealDB V1, por medio del servidor |
| Claves en `.env` | `THEMEALDB_API_KEY` y `DJANGO_SECRET_KEY` |
| `.env` fuera de GitHub | `.gitignore`; se comparte sólo `.env.example` |
| Seguridad | Hash PBKDF2 de Django, CSRF, sesiones HttpOnly, ORM, CSP y favoritos por propietario |
| Web services | API propia de recetas y favoritos con Django REST Framework |

## API externa

Documentación oficial: https://www.themealdb.com/docs_api_guide.php

TheMealDB proporciona la **clave pública de prueba `1`**, gratuita para desarrollo y aprendizaje. Está configurada en `.env`, no en el JavaScript ni en las plantillas. No se necesita registrar una cuenta ni introducir una tarjeta para probar este proyecto educativo. Para publicación pública, revisar las condiciones actuales del proveedor y obtener la clave apropiada.

El navegador consulta `/api/recetas/`; Django obtiene la clave desde `.env`, consulta TheMealDB por HTTPS, normaliza los datos y devuelve JSON sin la clave. Se usa un tiempo máximo de espera, caché de 5 minutos y mensajes de error controlados. La búsqueda requiere conexión a Internet. Los favoritos ya guardados se listan desde SQLite.

TheMealDB mantiene nombres, ingredientes e instrucciones principalmente en inglés. Prueba **pasta**, **chicken**, **salad**, **cake** o **Arrabiata**. Los accesos rápidos en español envían búsquedas compatibles. No se presenta contenido ficticio si falla el proveedor.

## Servicio REST propio

| Método | Ruta | Acceso | Resultado |
|---|---|---|---|
| GET | `/api/recetas/?q=pasta` | Público | Lista y cantidad de recetas |
| GET | `/api/recetas/52771/` | Público | Detalle normalizado |
| GET | `/api/favoritos/` | Sesión | Favoritos del usuario actual |
| POST | `/api/favoritos/` | Sesión + CSRF | Guardar `{"meal_id":"52771"}` |
| DELETE | `/api/favoritos/52771/` | Sesión + CSRF | Quitar un favorito propio |

Códigos: 200 consulta/registro ya existente, 201 favorito creado, 204 eliminado, 400 entrada inválida, 403 sin sesión/CSRF, 404 inexistente, 429 límite de solicitudes y 503 proveedor no disponible. El registro web devuelve los errores de campos en la misma pantalla.

## Validación y seguridad

- Nombre: de 2 a 80 caracteres, al menos 2 letras (incluidos acentos), sin números ni caracteres invisibles; espacios, guiones o apóstrofos simples entre letras.
- Correo válido y único, normalizado a minúsculas. Máximo 150 caracteres. Se comprueba formato estricto y dominio con capacidad de recibir correo mediante DNS sobre HTTPS (Cloudflare y Google como respaldo); un fallo temporal exige reintentar. Se aceptan dominios propios válidos, sin limitar a proveedores conocidos. Los dominios verificados se conservan en caché una hora; no se guarda el correo en esa caché.
- Contraseña: de 12 a 128 caracteres, mayúscula, minúscula y número; sin secuencias obvias, repeticiones de cuatro caracteres ni caracteres invisibles; validadores Django contra contraseñas comunes, numéricas o similares a datos del usuario. Confirmación obligatoria.
- Aviso de privacidad con aceptación obligatoria; sin persistencia de la fecha de consentimiento. Para un uso público se debe ampliar ese registro.
- Contraseñas mediante `set_password()`/`UserCreationForm`, nunca texto plano.
- Consultas parametrizadas mediante el ORM, escape de plantillas y `textContent` al mostrar datos de la API.
- CSRF en registro, ingreso, cierre de sesión y escrituras autenticadas. Cierre de sesión sólo por POST.
- Sesiones del servidor; cookie HttpOnly, SameSite=Lax, duración máxima de 2 horas y fin al cerrar navegador.
- Cada consulta y borrado de favoritos filtra por el usuario autenticado; no se aceptan IDs de propietario del cliente. Guardar verifica la receta en la API.
- Cabeceras CSP, protección contra iframes, `nosniff` y sin caché de páginas autenticadas. No se usa CORS abierto.
- Límite educativo de solicitudes REST e intentos de autenticación por IP. La caché local funciona para una instancia de desarrollo: en producción requiere una caché compartida y protección de infraestructura.
- El servidor de desarrollo usa HTTP local; **no se afirma que HTTP local esté cifrado**. En producción usar HTTPS, `DJANGO_DEBUG=False`, dominios concretos, `DJANGO_HTTPS=True`, un servidor WSGI adecuado y gestión de secretos. No desplegar `runserver` como servidor público.

## Instalar en otra computadora

Requiere Python 3.10 o superior y conexión a Internet. Abre una terminal dentro de esta carpeta:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Reemplaza `DJANGO_SECRET_KEY` en `.env` con una clave aleatoria generada localmente:

```powershell
.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Conserva `THEMEALDB_API_KEY=1` para la demostración académica. Después:

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

`requirements.txt` contiene rangos de versiones compatibles; `requirements-lock.txt` conserva las versiones exactas instaladas y verificadas en esta entrega. Puede usarse en lugar del primero.

## Pruebas

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py test
```

Las pruebas crean una base temporal y simulan la API externa: no dependen de Internet ni alteran tus usuarios. Cubren validación, correos duplicados, hash, sesiones, CSRF, límites, autorización, favoritos idempotentes y fallas del proveedor. Para revisar la conexión real, abre `/api/recetas/?q=pasta` mientras ejecutas el servidor.

Recorrido manual: inicio → explorar → buscar → detalle → registro → guardar favorito → favoritos → salir → volver a ingresar. Probar también correo inválido, contraseñas diferentes, búsqueda sin resultados y tamaño de celular.

## Administración y datos

Para administrar usuarios locales, crea tu cuenta de administrador (sin credenciales predefinidas):

```powershell
.venv\Scripts\python.exe manage.py createsuperuser
```

Accede a `/admin/`. El administrador puede corregir o eliminar usuarios; eliminar un usuario elimina sus favoritos por cascada. El código entregado no contiene una función de recuperación de contraseña por correo.

## Qué subir a GitHub

Subir código, plantillas, archivos estáticos, migraciones, documentación y `.env.example`. **No subir** `.env`, `.venv`, `db.sqlite3` ni archivos de caché: están excluidos en `.gitignore`. No se ha publicado ni enviado este proyecto a un repositorio remoto.

## Estructura

```text
Actividad 5/
├── config/              Configuración y rutas principales
├── recipes/             Modelos, formularios, vistas, API, servicios y pruebas
│   └── migrations/      Esquema de favoritos
├── templates/           Pantallas Django
├── static/              Estilos, JavaScript e imagen local de portada
├── .env                 Claves locales (ignorado)
├── .env.example         Variables sin secretos privados
├── .gitignore
├── iniciar.bat
├── manage.py
├── requirements.txt
└── README.md
```

Fotografía de portada y recetas: TheMealDB; ver `static/img/ATTRIBUTION.md`. La interfaz utiliza tipografías del sistema y funciona sin CDN de estilos ni bibliotecas de frontend.

## Refuerzo de validación del registro

Se utiliza `email-validator` y DNS para comprobar la capacidad del dominio de recibir correo. No se envía el correo completo a servicios de verificación externos; DNS sobre HTTPS consulta únicamente el dominio a Cloudflare (o Google como respaldo), con verificación TLS y espera limitada. No se confirma la existencia del buzón ni su propiedad: se requeriría implementar un correo de activación con enlace temporal. No se envían mensajes en este proyecto. El registro ahora requiere conexión para verificar dominios nuevos; el inicio de sesión conserva su funcionamiento sin esta consulta para no bloquear cuentas existentes. Las cuentas creadas antes del cambio no se borran ni se modifican.

Referencia técnica: https://github.com/JoshData/python-email-validator
