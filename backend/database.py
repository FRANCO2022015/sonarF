"""
NewsHub - database.py
Modulo de base de datos SQLite para el portal de noticias.

NOTA: Este archivo contiene errores INTENCIONALES para experimentacion con SonarQube:
  - [VULN] Credenciales hardcodeadas (Secret key, admin password)
  - [VULN] Consulta SQL vulnerable a inyeccion SQL
  - [SMELL] Codigo duplicado (funcion format_date repetida en utils.py)
  - [SMELL] Importaciones no utilizadas
"""

import sqlite3
import os          # SMELL: modulo importado pero nunca utilizado
import hashlib
import math        # SMELL: modulo importado pero nunca utilizado
from datetime import datetime

# ============================================================
# VULNERABILITY: Secretos Hardcodeados (Security Hotspot)
# Sonar deberia detectar credenciales en texto plano.
# ============================================================
SECRET_KEY = "super_secret_jwt_key_12345"   # VULN: hardcoded secret
ADMIN_PASSWORD = "admin123"                  # VULN: hardcoded password
DB_PASSWORD = "db_pass_newshub"              # VULN: hardcoded db credential

DB_NAME = "newshub.db"


def get_connection():
    """Obtiene una conexion a la base de datos SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos con tablas y datos de prueba."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            author TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'reader'
        );
    """)

    # Insertar noticias de prueba
    cursor.execute("SELECT COUNT(*) FROM articles")
    if cursor.fetchone()[0] == 0:
        sample_articles = [
            ("Tecnologia Cambia el Mundo en 2025",
             "La inteligencia artificial sigue avanzando a pasos agigantados. Nuevos modelos de lenguaje prometen revolucionar la industria tech. Las empresas lideres como Google, OpenAI y Anthropic compiten ferozmente por el liderazgo en este campo.",
             "tecnologia", "Admin NewsHub"),
            ("Clima Extremo Afecta Regiones del Sur",
             "Las lluvias torrenciales han causado inundaciones en multiples provincias. Los equipos de emergencia trabajan sin descanso para evacuar a los afectados. Se esperan mas lluvias durante la proxima semana segun el servicio meteorologico nacional.",
             "clima", "Redaccion"),
            ("Economia: El Peso Sube Frente al Dolar",
             "Los mercados financieros reaccionaron positivamente a las nuevas medidas economicas anunciadas. Analistas preveen una tendencia alcista durante los proximos meses si se mantienen las politicas actuales.",
             "economia", "Equipo Financiero"),
            ("Deportes: Nacional Campeon Nacional 2025",
             "El equipo logro el titulo despues de una temporada emocionante llena de sorpresas. El entrenador destaco el esfuerzo colectivo y la dedicacion de todos los jugadores durante la celebracion.",
             "deportes", "Deportes NewsHub"),
            ("Ciencia: Descubren Nueva Especie en Amazonia",
             "Un equipo de biologos internacionales identifico una nueva especie de anfibio en la selva amazonica. El hallazgo fue publicado en la prestigiosa revista Nature y representa un avance significativo para la biodiversidad.",
             "ciencia", "Ciencia y Naturaleza"),
        ]
        cursor.executemany(
            "INSERT INTO articles (title, content, category, author) VALUES (?, ?, ?, ?)",
            sample_articles
        )

        # Insertar comentarios de prueba
        sample_comments = [
            (1, "Juan Perez", "Excelente articulo! Muy informativo."),
            (1, "Maria Lopez", "Gracias por la informacion, muy util!"),
            (2, "Carlos Ruiz", "Preocupante la situacion climatica..."),
            (3, "Ana Gomez", "Buenas noticias para la economia!"),
            (4, "Pedro Martinez", "Merecido campeonato, gran temporada!"),
        ]
        cursor.executemany(
            "INSERT INTO comments (article_id, author, content) VALUES (?, ?, ?)",
            sample_comments
        )

        # VULNERABILITY: Password guardado sin hashing real (en texto plano expuesto)
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", ADMIN_PASSWORD, "admin")   # VULN: contraseña sin hashear
        )
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
            ("redactor", "redactor123", "editor")  # VULN: credencial hardcodeada
        )

    conn.commit()
    conn.close()


# ============================================================
# VULNERABILITY: SQL Injection
# La funcion de busqueda concatena directamente el input del usuario
# en la query SQL sin parametrizar. Sonar deberia detectarlo.
# ============================================================
def search_articles(query: str):
    """
    Busca articulos por titulo.
    ATENCION: VULNERABLE A INYECCION SQL - NO USAR EN PRODUCCION.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # VULN: SQL Injection - concatenacion directa sin parametros
    sql = "SELECT * FROM articles WHERE title LIKE '%" + query + "%' OR content LIKE '%" + query + "%'"
    cursor.execute(sql)  # noqa

    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_all_articles():
    """Retorna todos los articulos ordenados por fecha de creacion."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY created_at DESC")
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def get_article_by_id(article_id: int):
    """Retorna un articulo especifico por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_comments_by_article(article_id: int):
    """Retorna todos los comentarios de un articulo especifico."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM comments WHERE article_id = ? ORDER BY created_at ASC",
        (article_id,)
    )
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]


def add_comment(article_id: int, author: str, content: str):
    """Agrega un nuevo comentario a un articulo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (article_id, author, content) VALUES (?, ?, ?)",
        (article_id, author, content)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def increment_views(article_id: int):
    """Incrementa el contador de vistas de un articulo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE articles SET views = views + 1 WHERE id = ?",
        (article_id,)
    )
    conn.commit()
    conn.close()


def get_user_by_username(username: str):
    """
    Obtiene un usuario por nombre de usuario.
    ATENCION: Retorna la contrasena en texto plano (vulnerability).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ============================================================
# SMELL: Codigo Duplicado
# Esta funcion existe identica en utils.py (duplicacion deliberada).
# ============================================================
def format_date(date_str: str) -> str:
    """Formatea una fecha de string a formato legible. (DUPLICADO en utils.py)"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:   # SMELL: captura generica de Exception
        pass            # SMELL: silencia el error completamente
    return date_str
