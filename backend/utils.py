"""
NewsHub - utils.py
Modulo de utilidades y logica de negocio para el portal de noticias.

NOTA: Este archivo contiene errores INTENCIONALES para experimentacion con SonarQube:
  - [SMELL] Alta complejidad ciclomatica en calcular_relevancia()
  - [BUG]   Codigo inalcanzable (unreachable code)
  - [BUG]   Parametro mutable por defecto (mutable default argument)
  - [SMELL] Variables declaradas pero nunca utilizadas
  - [SMELL] Codigo duplicado (format_date identico a database.py)
  - [SMELL] Importaciones no usadas
"""

import json       # SMELL: importado pero nunca utilizado
import re         # SMELL: importado pero nunca utilizado
import sys        # SMELL: importado pero nunca utilizado
from datetime import datetime

# SMELL: Constantes "magicas" (magic numbers) sin nombre descriptivo
RELEVANCE_THRESHOLD = 50
MAX_COMMENTS = 100


# ============================================================
# BUG: Parametro Mutable por Defecto (Mutable Default Argument)
# En Python, las listas como argumento por defecto se comparten
# entre todas las llamadas a la funcion. Sonar debe detectarlo.
# ============================================================
def build_article_tags(title: str, extra_tags: list = []):
    """
    Genera lista de tags para un articulo.
    BUG: `extra_tags=[]` es un parametro mutable por defecto.
    """
    tags = extra_tags   # BUG: modifica la lista compartida entre llamadas
    keywords = title.lower().split()
    for word in keywords:
        if len(word) > 4:
            tags.append(word)
    return tags


# ============================================================
# SMELL: Alta Complejidad Ciclomatica
# Esta funcion tiene demasiados condicionales anidados.
# Sonar marcara la complejidad como excesiva.
# ============================================================
def calcular_relevancia(article: dict) -> int:
    """
    Calcula un puntaje de relevancia para un articulo.
    SMELL: Complejidad ciclomatica muy alta (exceso de if/elif/else anidados).
    """
    score = 0
    views = article.get("views", 0)
    category = article.get("category", "")
    title = article.get("title", "")
    content = article.get("content", "")
    author = article.get("author", "")

    unused_variable = "esto nunca se usa"  # SMELL: variable declarada y nunca leida

    # Puntaje por vistas
    if views > 1000:
        if views > 5000:
            if views > 10000:
                score += 50
            else:
                score += 35
        else:
            score += 20
    else:
        if views > 500:
            score += 10
        else:
            if views > 100:
                score += 5
            else:
                score += 0

    # Puntaje por categoria
    if category == "tecnologia":
        score += 15
    elif category == "economia":
        score += 12
    elif category == "deportes":
        score += 10
    elif category == "ciencia":
        score += 14
    elif category == "clima":
        score += 8
    elif category == "politica":
        score += 11
    else:
        if category == "entretenimiento":
            score += 7
        elif category == "salud":
            score += 13
        else:
            score += 3

    # Puntaje por longitud del contenido
    if len(content) > 500:
        if len(content) > 1000:
            if len(content) > 2000:
                score += 20
            else:
                score += 15
        else:
            score += 10
    else:
        score += 2

    # Puntaje por titulo
    if len(title) > 10:
        if "exclusivo" in title.lower():
            score += 25
        elif "urgente" in title.lower():
            score += 20
        elif "breaking" in title.lower():
            score += 18
        else:
            score += 5
    else:
        score += 0

    # Puntaje por autor conocido
    if author == "Admin NewsHub":
        score += 10
    elif author == "Redaccion":
        score += 8
    else:
        if author != "":
            score += 3
        else:
            score += 0

    return score

    # ============================================================
    # BUG: Codigo Inalcanzable (Unreachable Code)
    # Todo lo siguiente a `return` jamas se ejecutara.
    # Sonar deberia marcarlo como bug.
    # ============================================================
    print("Calculando bono extra...")   # BUG: nunca se ejecuta
    bonus = score * 0.1                 # BUG: nunca se ejecuta
    score += bonus                      # BUG: nunca se ejecuta
    return score                        # BUG: segundo return inalcanzable


def is_trending(article: dict) -> bool:
    """Determina si un articulo es tendencia segun su relevancia."""
    relevance = calcular_relevancia(article)
    if relevance > RELEVANCE_THRESHOLD:
        return True
    return False    # SMELL: podria simplificarse como `return relevance > RELEVANCE_THRESHOLD`


def get_article_summary(content: str, max_length: int = 150) -> str:
    """Retorna un resumen truncado del contenido del articulo."""
    result = ""         # SMELL: variable innecesaria, se podria retornar directamente
    if len(content) > max_length:
        result = content[:max_length] + "..."
    else:
        result = content
    return result


# ============================================================
# SMELL: Codigo Duplicado
# Esta funcion es identica a la de database.py.
# Sonar lo detectara como duplicacion de codigo.
# ============================================================
def format_date(date_str: str) -> str:
    """Formatea una fecha de string a formato legible. (DUPLICADO en database.py)"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:   # SMELL: captura generica de Exception
        pass            # SMELL: silencia el error completamente
    return date_str


def count_words(text: str) -> int:
    """Cuenta la cantidad de palabras en un texto."""
    words = text.split()
    total = len(words)
    extra_count = 0     # SMELL: variable declarada pero nunca usada
    return total


def validate_comment(content: str) -> bool:
    """Valida que un comentario tenga contenido valido."""
    if content is None:
        return False
    if content == "":
        return False
    if len(content) < 3:
        return False
    if len(content) > 1000:
        return False
    return True     # SMELL: todos estos ifs podrian simplificarse con una sola expresion
