"""
NewsHub - main.py
Servidor principal de la API FastAPI para el portal de noticias.

NOTA: Este archivo contiene errores INTENCIONALES para experimentacion con SonarQube:
  - [VULN] CORS configurado sin restricciones (allow_origins=["*"])
  - [VULN] JWT con secreto hardcodeado y algoritmo debil
  - [BUG]  Manejo incorrecto de excepciones (captura generica silenciada)
  - [SMELL] Importacion no utilizada
  - [SMELL] Variables no usadas dentro de funciones
"""

import jwt           # para generacion de tokens
import time          # SMELL: importado pero no utilizado directamente en logica propia
import logging       # SMELL: configurado pero nunca usado para loguear realmente
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    import database
    import utils
except ModuleNotFoundError:
    from backend import database, utils


# ============================================================
# Configuracion de la Aplicacion
# ============================================================
app = FastAPI(
    title="NewsHub API",
    description="API para el portal de noticias NewsHub",
    version="1.0.0"
)

# ============================================================
# VULNERABILITY: CORS sin restricciones (Security Hotspot)
# allow_origins=["*"] permite peticiones desde CUALQUIER origen.
# Sonar deberia marcarlo como Security Hotspot.
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # VULN: permite cualquier origen sin filtro
    allow_credentials=True,
    allow_methods=["*"],        # VULN: permite todos los metodos HTTP
    allow_headers=["*"],        # VULN: permite todos los headers
)

# ============================================================
# VULNERABILITY: Secreto JWT Hardcodeado
# Usando el mismo secreto hardcodeado de database.py directamente.
# ============================================================
JWT_SECRET = "super_secret_jwt_key_12345"   # VULN: hardcoded secret (duplicado)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Configuracion de logging (declarada pero usada minimalamente)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("newshub")


# ============================================================
# Modelos Pydantic
# ============================================================
class CommentCreate(BaseModel):
    author: str
    content: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ArticleCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"
    author: str


# ============================================================
# Eventos de Inicio
# ============================================================
@app.on_event("startup")
async def startup_event():
    """Inicializa la base de datos al arrancar el servidor."""
    database.init_db()
    logger.info("NewsHub API iniciada correctamente.")


# ============================================================
# Endpoints - Articulos
# ============================================================
@app.get("/api/articles", tags=["Articulos"])
async def get_articles():
    """
    Retorna todos los articulos disponibles con su puntaje de relevancia.
    """
    try:
        articles = database.get_all_articles()
        enriched = []
        for article in articles:
            article["relevance_score"] = utils.calcular_relevancia(article)
            article["is_trending"] = utils.is_trending(article)
            article["summary"] = utils.get_article_summary(article["content"])
            article["word_count"] = utils.count_words(article["content"])
            enriched.append(article)
        return {"articles": enriched, "total": len(enriched)}
    except Exception as e:  # SMELL: captura generica - deberia ser mas especifica
        # BUG: El mensaje de error expone detalles internos del servidor
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/api/articles/{article_id}", tags=["Articulos"])
async def get_article(article_id: int):
    """Retorna un articulo especifico por su ID e incrementa el contador de vistas."""
    try:
        article = database.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Articulo no encontrado")

        database.increment_views(article_id)
        article["views"] += 1

        comments = database.get_comments_by_article(article_id)
        article["comments"] = comments
        article["relevance_score"] = utils.calcular_relevancia(article)

        unused_data = {"extra": "info"}  # SMELL: variable creada pero nunca usada

        return article
    except HTTPException:
        raise
    except Exception:           # BUG: captura todo y silencia el error real
        pass                    # BUG: no retorna nada util al cliente


@app.get("/api/search", tags=["Articulos"])
async def search_articles(q: str = Query(..., min_length=1, description="Termino de busqueda")):
    """
    Busca articulos por titulo o contenido.
    ATENCION: El backend llama a una funcion con SQL Injection.
    """
    # VULN: La funcion search_articles en database.py es vulnerable a SQL Injection
    results = database.search_articles(q)
    return {"results": results, "query": q, "count": len(results)}


# ============================================================
# Endpoints - Comentarios
# ============================================================
@app.get("/api/articles/{article_id}/comments", tags=["Comentarios"])
async def get_comments(article_id: int):
    """Retorna todos los comentarios de un articulo."""
    comments = database.get_comments_by_article(article_id)
    return {"comments": comments, "total": len(comments)}


@app.post("/api/articles/{article_id}/comments", tags=["Comentarios"])
async def add_comment(article_id: int, comment: CommentCreate):
    """
    Agrega un comentario a un articulo.
    El contenido NO es sanitizado antes de guardarlo (riesgo XSS en frontend).
    """
    article = database.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Articulo no encontrado")

    # SMELL: Validacion minima - no se sanea el HTML del comentario
    if not utils.validate_comment(comment.content):
        raise HTTPException(status_code=400, detail="Comentario invalido")

    new_id = database.add_comment(article_id, comment.author, comment.content)
    return {"message": "Comentario agregado exitosamente", "comment_id": new_id}


# ============================================================
# Endpoints - Autenticacion
# ============================================================
@app.post("/api/login", tags=["Autenticacion"])
async def login(credentials: LoginRequest):
    """
    Autenticacion de usuarios.
    VULNERABILIDADES: Comparacion de contrasena en texto plano, JWT con secreto debil.
    """
    user = database.get_user_by_username(credentials.username)

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    # VULN: Comparacion de contrasena en texto plano (sin hashing)
    if credentials.password != user["password"]:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    # VULN: JWT con secreto hardcodeado y sin claims de seguridad robustos
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # VULN: La respuesta incluye datos sensibles del usuario
    return {
        "token": token,
        "username": user["username"],
        "role": user["role"],
        "password_hint": user["password"][:3] + "***"  # VULN: expone parte de la contrasena
    }


# ============================================================
# Endpoints - Estadisticas
# ============================================================
@app.get("/api/stats", tags=["Estadisticas"])
async def get_stats():
    """Retorna estadisticas generales del portal."""
    try:
        articles = database.get_all_articles()
        total_articles = len(articles)
        total_views = sum(a["views"] for a in articles)
        categories = {}

        for article in articles:
            cat = article.get("category", "general")
            if cat in categories:
                categories[cat] += 1
            else:
                categories[cat] = 1

        trending = [a for a in articles if utils.is_trending(a)]

        return {
            "total_articles": total_articles,
            "total_views": total_views,
            "categories": categories,
            "trending_count": len(trending)
        }
    except Exception:   # SMELL: captura generica sin manejo
        pass            # BUG: silencia el error, el cliente recibe None
