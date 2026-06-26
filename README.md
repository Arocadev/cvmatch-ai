# CVMatch AI

> Herramienta personal de búsqueda de empleo con IA | Personal AI-powered job search tool

---

## 🇪🇸 Español

**CVMatch AI** te ayuda a buscar, organizar y analizar ofertas de empleo usando inteligencia artificial. Sube tu CV, obtén un porcentaje de compatibilidad con cada oferta, descubre qué palabras clave faltan y genera el texto de tu CV adaptado para cada puesto.

---

### ✨ Funcionalidades

- 🔍 **Búsqueda multi-fuente** — Adzuna (España, UK, USA), Jooble (Internacional), Arbeitnow (Europa)
- 📋 **Resumen de oferta con IA** — stack, modalidad, experiencia y salario extraídos automáticamente
- 📊 **Análisis de CV** — porcentaje de compatibilidad + palabras clave que faltan + mejoras concretas
- 📝 **Generador de CV adaptado** — reescribe el texto de tu CV para cada oferta específica
- 🗂️ **Gestión de ofertas** — estados Nueva / Vista / Guardada / Descartada
- 🌍 **Interfaz bilingüe** — Español / Inglés
- 🔒 **Acceso protegido** — control de acceso con contraseña

---

### 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Django 6 + Python 3.14 |
| Base de datos | PostgreSQL 16 |
| IA | Groq (llama-3.3-70b-versatile) |
| APIs de empleo | Adzuna, Jooble, Arbeitnow |
| Lectura de PDF | PyMuPDF (fitz) |
| Frontend | Django Templates + CSS |

---

### 📁 Estructura del proyecto

```
cvmatch-ai/
├── jobtracker/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── ofertas/
│   ├── api.py
│   ├── cv.py
│   ├── middleware.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── static/
│   │   └── ofertas/
│   │       └── style.css
│   └── templates/
│       └── ofertas/
│           ├── acceso.html
│           ├── analisis.html
│           ├── buscador.html
│           ├── cv_generado.html
│           ├── detalle.html
│           ├── inicio.html
│           └── lista.html
├── .env.example
├── requirements.txt
└── manage.py
```

---

### 🚀 Instalación

```bash
git clone https://github.com/Arocadev/cvmatch-ai.git
cd cvmatch-ai

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edita .env con tus API keys y credenciales

python manage.py migrate
python manage.py runserver
```

---

### 🔑 Variables de entorno

```env
ADZUNA_APP_ID=        # https://developer.adzuna.com
ADZUNA_APP_KEY=       # https://developer.adzuna.com
JOOBLE_API_KEY=       # https://jooble.org/api/about
GROQ_API_KEY=         # https://console.groq.com
APP_PASSWORD=         # Contraseña de acceso a la app
DB_NAME=              # Nombre de la base de datos PostgreSQL
DB_USER=              # Usuario PostgreSQL
DB_PASSWORD=          # Contraseña PostgreSQL
DB_HOST=localhost
DB_PORT=5432
```

---

## 🌐 English

**CVMatch AI** helps you search, organize and analyze job offers using AI. Upload your CV and get a compatibility score, keyword suggestions and an adapted CV text for each offer — all in one place.

---

### ✨ Features

- 🔍 **Multi-source job search** — Adzuna (Spain, UK, US), Jooble (International), Arbeitnow (Europe)
- 📋 **AI-generated offer summary** — stack, modality, experience, salary extracted automatically
- 📊 **CV compatibility analysis** — percentage match + missing keywords + concrete improvements
- 📝 **Adapted CV generator** — rewrite your CV text for each specific offer
- 🗂️ **Offer management** — New / Viewed / Saved / Discarded states
- 🌍 **Bilingual interface** — Spanish / English
- 🔒 **Password protected** — simple access control

---

### 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6 + Python 3.14 |
| Database | PostgreSQL 16 |
| AI | Groq (llama-3.3-70b-versatile) |
| Job APIs | Adzuna, Jooble, Arbeitnow |
| PDF parsing | PyMuPDF (fitz) |
| Frontend | Django Templates + CSS |

---

### 📁 Project Structure

```
cvmatch-ai/
├── jobtracker/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── ofertas/
│   ├── api.py
│   ├── cv.py
│   ├── middleware.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── static/
│   │   └── ofertas/
│   │       └── style.css
│   └── templates/
│       └── ofertas/
│           ├── acceso.html
│           ├── analisis.html
│           ├── buscador.html
│           ├── cv_generado.html
│           ├── detalle.html
│           ├── inicio.html
│           └── lista.html
├── .env.example
├── requirements.txt
└── manage.py
```

---

### 🚀 Installation

```bash
git clone https://github.com/Arocadev/cvmatch-ai.git
cd cvmatch-ai

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys and database credentials

python manage.py migrate
python manage.py runserver
```

---

### 🔑 Environment Variables

```env
ADZUNA_APP_ID=        # https://developer.adzuna.com
ADZUNA_APP_KEY=       # https://developer.adzuna.com
JOOBLE_API_KEY=       # https://jooble.org/api/about
GROQ_API_KEY=         # https://console.groq.com
APP_PASSWORD=         # Access password for the app
DB_NAME=              # PostgreSQL database name
DB_USER=              # PostgreSQL user
DB_PASSWORD=          # PostgreSQL password
DB_HOST=localhost
DB_PORT=5432
```

---

## 👤 Autor / Author

**Alejandro Rodríguez Calabuig** — [github.com/Arocadev](https://github.com/Arocadev) · [LinkedIn](https://linkedin.com/in/alejandro-rodriguez-calabuig)

---

## 📄 Licencia / License

Proyecto personal — no licenciado para uso comercial.  
Personal project — not licensed for commercial use.
