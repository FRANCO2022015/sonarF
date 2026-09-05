# NewsHub - Portal de Noticias 📰

---

##  Estructura del Proyecto

```
sonarF/
├── sonar-project.properties    # Configuración para SonarScanner
├── README.md
├── backend/
│   ├── requirements.txt        # Dependencias Python
│   ├── database.py             # Base de datos SQLite (con errores)
│   ├── utils.py                # Utilidades y lógica (con errores)
│   └── main.py                 # API FastAPI principal (con errores)
└── frontend/
    ├── index.html              # Interfaz de usuario
    └── app.js                  # Lógica JavaScript (con errores)
```

---

##  Errores 

| # | Archivo | Categoría Sonar | Descripción |
|---|---------|-----------------|-------------|
| 1 | `database.py` | 🔴 Vulnerability | **SQL Injection**: función `search_articles()` concatena input del usuario directamente en SQL |
| 2 | `database.py` | 🔴 Vulnerability | **Hardcoded Secrets**: `SECRET_KEY`, `ADMIN_PASSWORD`, `DB_PASSWORD` en texto plano |
| 3 | `database.py` | 🔴 Vulnerability | **Contraseña sin hashear**: usuarios guardados con contraseña en texto plano |
| 4 | `database.py` | 🟡 Code Smell | **Importaciones no usadas**: `import os`, `import math` |
| 5 | `database.py` | 🟡 Code Smell | **Código Duplicado**: función `format_date()` idéntica en `utils.py` |
| 6 | `database.py` | 🟡 Code Smell | **Captura genérica**: `except Exception: pass` silencia errores |
| 7 | `utils.py` | 🔴 Bug | **Parámetro mutable por defecto**: `def build_article_tags(title, extra_tags=[])` |
| 8 | `utils.py` | 🔴 Bug | **Código Inalcanzable**: código y `return` después de un `return` previo |
| 9 | `utils.py` | 🟡 Code Smell | **Alta Complejidad Ciclomática**: función `calcular_relevancia()` con >15 ramas |
| 10 | `utils.py` | 🟡 Code Smell | **Variables no usadas**: `unused_variable`, `extra_count` declaradas pero nunca leídas |
| 11 | `utils.py` | 🟡 Code Smell | **Importaciones no usadas**: `import json`, `import re`, `import sys` |
| 12 | `utils.py` | 🟡 Code Smell | **Código Duplicado**: función `format_date()` idéntica a `database.py` |
| 13 | `main.py` | 🔴 Vulnerability | **CORS Permisivo**: `allow_origins=["*"]` sin restricciones de origen |
| 14 | `main.py` | 🔴 Vulnerability | **JWT Secret Hardcodeado**: `JWT_SECRET = "super_secret_jwt_key_12345"` |
| 15 | `main.py` | 🔴 Vulnerability | **Info Sensible en Respuesta**: endpoint `/login` devuelve `password_hint` |
| 16 | `main.py` | 🔴 Bug | **Captura silenciosa**: `except Exception: pass` en `get_article()` y `get_stats()` devuelve `None` |
| 17 | `main.py` | 🟡 Code Smell | **Variable no usada**: `unused_data` en `get_article()` |
| 18 | `app.js` | 🔴 Vulnerability | **XSS**: `innerHTML` con datos del servidor sin escapar (artículos y comentarios) |
| 19 | `app.js` | 🔴 Vulnerability | **XSS en Login**: `innerHTML` con `username` sin escapar |
| 20 | `app.js` | 🔴 Vulnerability | **Uso de `eval()`**: evaluación de expresión dinámica en `performSearch()` |
| 21 | `app.js` | 🟡 Code Smell | **Variables globales sin declarar**: `currentArticleId`, `userToken`, `allArticlesCache` sin `let/const` |
| 22 | `app.js` | 🟡 Code Smell | **`console.log` de depuración**: múltiples llamadas sin eliminar |
| 23 | `app.js` | 🔴 Bug | **Comparación débil `==`**: usar `==` en lugar de `===` en JavaScript |
| 24 | `app.js` | 🟡 Code Smell | **Código Duplicado**: funciones `formatDate()` y `getFormattedDate()` idénticas |
| 25 | `app.js` | 🟡 Code Smell | **Función vacía/inútil**: `setupCommentForm()` no hace nada útil |

---

