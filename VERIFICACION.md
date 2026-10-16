# Verificación de la entrega

Fecha local: 14 de octubre de 2026.

- Django: comprobación de configuración sin errores.
- Migraciones: aplicadas; sin cambios de modelos pendientes.
- Pruebas automatizadas: **30 de 30 aprobadas**.
- JavaScript: comprobación de sintaxis aprobada con Node.js.
- TheMealDB: consulta real HTTP 200 e imagen de portada descargada correctamente.
- Servidor WSGI temporal: inicio, CSS, JavaScript y API de búsqueda respondieron HTTP 200.
- Clave privada: sólo en `.env`; no aparece en código, plantillas ni archivos públicos.
- Exclusión: `.gitignore` contiene `.env`, `.venv/`, base SQLite y cachés.
- Cuentas persistidas en la entrega: ninguna. Las pruebas usan una base temporal.
- Revisión visual interactiva: pendiente; la herramienta de navegador no pudo acceder al servidor local de este entorno. No se afirma haber verificado capturas o interacción visual en escritorio/móvil.

Para la comprobación manual, ejecutar `iniciar.bat`, abrir http://127.0.0.1:8000/ y recorrer inicio, búsqueda, registro, guardado de favoritos e ingreso. Revisar también el ancho de celular.

No se publicó en Internet ni se envió a GitHub. El proyecto se entrega localmente como se solicitó.

## Refuerzo del registro

- Se rechazó mediante una consulta real el ejemplo `sdasd@sexmail.xom` por dominio inexistente.
- Se aceptó el formato y dominio de una dirección de prueba en gmail.com sin crear cuenta ni enviar correo.
- Se añadieron pruebas de nombres, contraseñas, correo inválido, fallo de dominio y resolución indeterminada.
- Consulta del dominio mediante DNS sobre HTTPS, con plazo limitado y caché; no se consulta ni comprueba la existencia del buzón.
- Se mantienen las cuentas y los favoritos ya existentes.
