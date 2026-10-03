# BURBUCOLA — Aula virtual v2

## Qué incluye
- Web pública de la empresa ficticia Burbucola.
- Panel privado de MJA.
- Comunicados publicados por MJA.
- Creación y borrado de casos de Derecho del Trabajo.
- Área de trabajadores.
- Identificación sencilla del alumno por nombre.
- Envío y actualización de respuestas a casos.
- Archivo de documentos mediante enlaces públicos.
- Base de datos SQLite.
- Plantilla de despliegue para Render.

## Ejecutar en local

1. Instala Python 3.11+.
2. Abre una terminal en esta carpeta.
3. Ejecuta:
   python -m venv .venv
   - Windows: .venv\Scripts\activate
   - macOS/Linux: source .venv/bin/activate
4. Instala dependencias:
   pip install -r requirements.txt
5. Arranca:
   python app.py
6. Abre http://127.0.0.1:5000

## Acceso de MJA
Contraseña inicial: burbucola

Para producción, define:
TEACHER_PASSWORD=una-clave-larga-y-segura
SECRET_KEY=otra-clave-larga-y-aleatoria

## Publicarla en Internet
La forma más sencilla es crear una cuenta en Render, subir este proyecto a un repositorio de GitHub y crear un Web Service usando render.yaml.

IMPORTANTE SOBRE DATOS
La aplicación usa SQLite. En algunos servicios gratuitos el disco puede ser efímero, por lo que para un uso académico continuado conviene sustituir SQLite por PostgreSQL. La estructura de la aplicación está preparada para que esa migración sea posible.

## Siguiente evolución recomendada
- cuentas individuales para alumnos;
- roles profesor/alumno;
- PostgreSQL;
- subida real de PDFs;
- calendario;
- rúbricas y calificación;
- feedback privado de MJA;
- notificaciones;
- historial de cambios;
- protección CSRF y endurecimiento de seguridad;
- integración con el dominio de la universidad.
