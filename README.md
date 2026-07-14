<div align="center">

# CVMatch AI

**Herramienta de búsqueda de empleo potenciada por IA**  
*AI-powered job search tool*

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-green?logo=django)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://postgresql.org)
[![Groq](https://img.shields.io/badge/AI-Groq-orange)](https://console.groq.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://docker.com)

</div>

---

## ¿Qué es CVMatch AI?

CVMatch AI es una aplicación web que combina búsqueda de empleo multi-fuente con inteligencia artificial para ayudarte a candidar de forma más efectiva. Busca ofertas en tiempo real, analiza la compatibilidad con tu CV, genera resúmenes automáticos y produce un CV adaptado a cada oferta en formato PDF profesional.

---

## ✨ Funcionalidades principales

### 🔍 Búsqueda de empleo multi-fuente
Busca simultáneamente en **Adzuna** (España, UK, USA), **Jooble** (Internacional) y **Arbeitnow** (Europa). Filtra por modalidad, experiencia y salario desde una sola pantalla.

### 📋 Resumen de oferta con IA
Analiza cualquier oferta y extrae automáticamente el stack tecnológico, modalidad de trabajo, años de experiencia requeridos y rango salarial.

### 📊 Análisis de compatibilidad CV ↔ Oferta
Sube tu CV y obtén un **porcentaje de compatibilidad**, las palabras clave que faltan y sugerencias de mejora concretas adaptadas a cada oferta.

### 📝 Generador de CV adaptado con IA
La IA reescribe tu CV completo en formato JSON estructurado, adaptando el lenguaje y priorizando las tecnologías más relevantes para cada oferta. El orden de secciones se ajusta automáticamente al perfil del candidato.

### 🎨 Generador de PDF — 5 plantillas profesionales

| Plantilla | Identidad | Ideal para |
|-----------|-----------|------------|
| **Classic** | Blanco y negro, sin decoración | Pasar filtros ATS |
| **Executive** | Azul marino + dorado, foto circular | Perfiles senior, consultoras |
| **Modern** | Sidebar oscuro + azul eléctrico | Desarrolladores, perfiles tech |
| **Editorial** | Serif, mucho espacio, minimalista | Perfiles senior, arquitectura |
| **One Page** | Verde oscuro, dos columnas compactas | Todo en una página |

Todas las plantillas generan PDFs con **WeasyPrint**, separando automáticamente TECNOLOGÍAS de HABILIDADES blandas, y adaptando el orden de secciones según el perfil.

### 🗂️ Gestión de ofertas
Panel lateral con estados **Nueva / Vista / Guardada / Descartada**. Preview de oferta sin navegar. Paginación y búsqueda activa guardada en sesión.

### 🔒 Seguridad
- Tokens Groq por usuario cifrados con **Fernet AES-256**
- Rate limiting en todas las rutas sensibles
- Sanitización de inputs y headers de seguridad
- 48 tests unitarios

### 🌍 Interfaz bilingüe
Español / Inglés con cambio de idioma persistente en sesión.

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6 + Python 3.12 |
| Base de datos | PostgreSQL 16 |
| Cache / Cola | Redis 7 + Celery |
| IA | Groq API (`openai/gpt-oss-120b`) |
| PDF | WeasyPrint + 5 plantillas HTML/CSS |
| APIs de empleo | Adzuna, Jooble, Arbeitnow |
| Lectura de PDF | PyMuPDF (fitz) |
| Servidor | Gunicorn |
| Contenedores | Docker + Docker Compose |
| Frontend | Django Templates + CSS custom |

---

## 📁 Estructura del proyecto

```
cvmatch-ai/
├── jobtracker/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── ofertas/
│   ├── api.py          # Integración Adzuna, Jooble, Arbeitnow
│   ├── cv.py           # Prompts IA: análisis, generación y mejora de CV
│   ├── pdf.py          # Generador PDF con WeasyPrint
│   ├── tasks.py        # Tareas Celery asíncronas
│   ├── security.py     # Rate limiting, sanitización, cifrado
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── static/
│   │   └── ofertas/
│   │       ├── style.css
│   │       ├── js/
│   │       │   └── crear_cv.js
│   │       └── pdf/
│   │           ├── classic.css
│   │           ├── executive.css
│   │           ├── modern.css
│   │           ├── editorial.css
│   │           └── compact.css
│   └── templates/
│       └── ofertas/
│           ├── pdf/
│           │   ├── classic.html
│           │   ├── executive.html
│           │   ├── modern.html
│           │   ├── editorial.html
│           │   └── compact.html
│           ├── cv_generado.html
│           ├── crear_cv.html
│           ├── analisis.html
│           ├── lista.html
│           └── ...
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

---

## 🚀 Instalación con Docker (recomendado)

```bash
git clone https://github.com/Arocadev/cvmatch-ai.git
cd cvmatch-ai
cp .env.example .env
# Edita .env con tus credenciales
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Accede en `http://localhost:8000`

---

## 🚀 Instalación local

```bash
git clone https://github.com/Arocadev/cvmatch-ai.git
cd cvmatch-ai
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tus credenciales
python manage.py migrate
python manage.py runserver
```

Para las tareas asíncronas necesitas Redis y Celery corriendo:
```bash
celery -A jobtracker worker --loglevel=info
```

---

## 🔑 Variables de entorno

```env
# Base de datos
DB_NAME=jobtracker
DB_USER=postgres
DB_PASSWORD=
DB_HOST=db          # 'db' en Docker, 'localhost' en local
DB_PORT=5432

# IA
GROQ_API_KEY=       # https://console.groq.com
GROQ_MODEL=openai/gpt-oss-120b

# APIs de empleo
ADZUNA_APP_ID=      # https://developer.adzuna.com
ADZUNA_APP_KEY=     # https://developer.adzuna.com
JOOBLE_API_KEY=     # https://jooble.org/api/about

# Seguridad
SECRET_KEY=
FERNET_KEY=         # Generado con Fernet.generate_key()
DEBUG=False

# Redis / Celery
REDIS_URL=redis://redis:6379/0
```

---

## 🧪 Tests

```bash
python manage.py test ofertas --verbosity=2
```

48 tests unitarios usando SQLite para evitar dependencia de PostgreSQL en CI.

---

## 🗺️ Roadmap

- [ ] Despliegue en Railway con dominio aroca.dev
- [ ] READMEs individuales por plantilla PDF
- [ ] Demo en vídeo
- [ ] Capturas de pantalla en README

---

## 👤 Autor

**Alejandro Rodríguez Calabuig**  
[github.com/ArocaDev](https://github.com/ArocaDev) · [LinkedIn](https://www.linkedin.com/in/alejandro-rodriguez-calabuig-a871a1230)

---

## 📄 Licencia

Proyecto personal — no licenciado para uso comercial.
