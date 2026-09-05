// ============================================================
// NewsHub - app.js
// Logica del frontend para el portal de noticias.
//
// NOTA: Este archivo contiene errores INTENCIONALES para
// experimentacion con SonarQube:
//   - [VULN] XSS: uso de innerHTML con contenido sin sanitizar
//   - [SMELL] Uso de eval() (practica extremadamente peligrosa)
//   - [SMELL] Variables globales sin declarar (sin let/const/var)
//   - [SMELL] console.log de depuracion no eliminados
//   - [SMELL] Codigo duplicado (funciones repetidas)
//   - [BUG]   Comparacion con == en lugar de === (tipo no estricto)
//   - [SMELL] Funcion con demasiados parametros
// ============================================================

const API_BASE = "http://localhost:8000/api";

// SMELL: Variable global no declarada formalmente con let/const
currentArticleId = null;   // SMELL: falta `let` o `const`
userToken = null;           // SMELL: falta `let` o `const`
allArticlesCache = [];      // SMELL: falta `let` o `const`

// ============================================================
// INICIALIZACION
// ============================================================
document.addEventListener("DOMContentLoaded", function () {
    console.log("NewsHub inicializado");  // SMELL: console.log de debug
    loadArticles();
    setupSearch();
    setupLoginForm();
    setupCommentForm();
});

// ============================================================
// CARGA DE ARTICULOS
// ============================================================
async function loadArticles() {
    try {
        console.log("Cargando articulos...");  // SMELL: console.log de debug
        const response = await fetch(`${API_BASE}/articles`);
        const data = await response.json();

        allArticlesCache = data.articles;
        console.log("Articulos recibidos:", data);  // SMELL: expone datos en consola

        renderArticlesList(data.articles);
        renderStats(data.articles);
    } catch (error) {
        console.error("Error al cargar articulos:", error);
        document.getElementById("articles-container").innerHTML =
            "<p class='error-msg'>Error al cargar las noticias. Verifica que el servidor este activo.</p>";
    }
}

// ============================================================
// RENDERIZADO DE ARTICULOS - VULNERABILIDAD XSS
// ============================================================
function renderArticlesList(articles) {
    const container = document.getElementById("articles-container");

    if (!articles || articles.length == 0) {  // BUG: == en lugar de ===
        container.innerHTML = "<p>No hay articulos disponibles.</p>";
        return;
    }

    let html = "";
    for (let i = 0; i < articles.length; i++) {
        const article = articles[i];
        const trending = article.is_trending ? '<span class="badge-trending">🔥 Tendencia</span>' : "";

        // VULN: XSS - El titulo y contenido del articulo se insertan directamente
        // en innerHTML sin ningun tipo de sanitizacion o escape de HTML.
        // Un atacante podria inyectar <script>alert('XSS')</script> en el titulo.
        html += `
            <article class="article-card" onclick="showArticle(${article.id})">
                <div class="article-header">
                    <span class="category-badge">${article.category}</span>
                    ${trending}
                </div>
                <h2 class="article-title">${article.title}</h2>
                <p class="article-summary">${article.summary}</p>
                <div class="article-meta">
                    <span>✍️ ${article.author}</span>
                    <span>👁️ ${article.views} vistas</span>
                    <span>📊 Relevancia: ${article.relevance_score}</span>
                    <span>📅 ${article.created_at}</span>
                </div>
            </article>
        `;
    }

    // VULN: innerHTML inyectando HTML generado con datos del servidor sin escapar
    container.innerHTML = html;  // VULN: XSS vulnerability aqui
}


// ============================================================
// DETALLE DE ARTICULO Y COMENTARIOS - XSS EN COMENTARIOS
// ============================================================
async function showArticle(articleId) {
    currentArticleId = articleId;

    try {
        const response = await fetch(`${API_BASE}/articles/${articleId}`);
        const article = await response.json();

        console.log("Articulo cargado:", article);  // SMELL: debug log

        const modal = document.getElementById("article-modal");
        const modalContent = document.getElementById("modal-content");

        let commentsHtml = "";
        if (article.comments && article.comments.length > 0) {
            article.comments.forEach(comment => {
                // VULN: XSS - El contenido del comentario se inserta sin escapar.
                // Un usuario malicioso puede escribir <img src=x onerror=alert('XSS')>
                // y se ejecutara cuando cualquier otro usuario vea el articulo.
                commentsHtml += `
                    <div class="comment">
                        <strong>${comment.author}</strong>
                        <span class="comment-date">${comment.created_at}</span>
                        <p>${comment.content}</p>
                    </div>
                `;  // VULN: XSS - comment.content sin sanitizar
            });
        } else {
            commentsHtml = "<p class='no-comments'>Sin comentarios aun. ¡Se el primero!</p>";
        }

        // VULN: todo el bloque HTML usa innerHTML con datos del servidor
        modalContent.innerHTML = `
            <button class="close-btn" onclick="closeModal()">✕ Cerrar</button>
            <div class="article-full">
                <span class="category-badge">${article.category}</span>
                <h1>${article.title}</h1>
                <div class="article-meta">
                    <span>✍️ ${article.author}</span>
                    <span>👁️ ${article.views} vistas</span>
                    <span>📅 ${article.created_at}</span>
                </div>
                <div class="article-body">
                    <p>${article.content}</p>
                </div>
                <section class="comments-section">
                    <h3>💬 Comentarios (${article.comments ? article.comments.length : 0})</h3>
                    <div id="comments-list">${commentsHtml}</div>
                    <div class="add-comment">
                        <h4>Agregar Comentario</h4>
                        <input type="text" id="comment-author" placeholder="Tu nombre" />
                        <textarea id="comment-content" placeholder="Escribe tu comentario aqui... (intenta con <b>negrita</b>)"></textarea>
                        <button onclick="submitComment()">Publicar Comentario</button>
                    </div>
                </section>
            </div>
        `;

        modal.style.display = "flex";
    } catch (error) {
        console.error("Error al cargar el articulo:", error);
    }
}


function closeModal() {
    document.getElementById("article-modal").style.display = "none";
    currentArticleId = null;
}


// ============================================================
// ENVIO DE COMENTARIOS
// ============================================================
async function submitComment() {
    const author = document.getElementById("comment-author").value;
    const content = document.getElementById("comment-content").value;

    if (author == "" || content == "") {    // BUG: == en lugar de ===
        alert("Por favor completa todos los campos.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/articles/${currentArticleId}/comments`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ author: author, content: content })
        });

        if (response.ok) {
            alert("Comentario publicado exitosamente!");
            showArticle(currentArticleId);  // recargar el articulo
        } else {
            alert("Error al publicar el comentario.");
        }
    } catch (error) {
        console.error("Error:", error);
    }
}


// ============================================================
// BUSQUEDA
// ============================================================
function setupSearch() {
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");

    if (searchBtn) {
        searchBtn.addEventListener("click", performSearch);
    }
    if (searchInput) {
        searchInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") performSearch();
        });
    }
}


async function performSearch() {
    const query = document.getElementById("search-input").value;

    if (query == "") {          // BUG: == en lugar de ===
        loadArticles();
        return;
    }

    try {
        console.log("Buscando:", query);    // SMELL: debug log
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        // SMELL: Uso de eval() - extremadamente peligroso
        // Sonar deberia detectar el uso de eval en cualquier contexto.
        const filterExpression = "data.results.length > 0";
        const hasResults = eval(filterExpression);  // SMELL/VULN: uso de eval()

        if (hasResults) {
            renderArticlesList(data.results);
            document.getElementById("search-results-count").textContent =
                `${data.count} resultado(s) para: "${query}"`;
        } else {
            document.getElementById("articles-container").innerHTML =
                `<p class='no-results'>No se encontraron articulos para "<strong>${query}</strong>".</p>`;
            document.getElementById("search-results-count").textContent = "Sin resultados";
        }
    } catch (error) {
        console.error("Error en busqueda:", error);
    }
}


// ============================================================
// ESTADISTICAS
// ============================================================
function renderStats(articles) {
    const statsEl = document.getElementById("stats-container");
    if (!statsEl) return;

    // SMELL: Codigo duplicado - misma logica de conteo de categorias que en el backend
    const categories = {};
    articles.forEach(a => {
        const cat = a.category || "general";
        if (categories[cat]) {
            categories[cat]++;
        } else {
            categories[cat] = 1;
        }
    });

    const totalViews = articles.reduce((sum, a) => sum + (a.views || 0), 0);
    const trending = articles.filter(a => a.is_trending).length;

    statsEl.innerHTML = `
        <div class="stat-item"><span class="stat-num">${articles.length}</span><span class="stat-label">Noticias</span></div>
        <div class="stat-item"><span class="stat-num">${totalViews}</span><span class="stat-label">Vistas Totales</span></div>
        <div class="stat-item"><span class="stat-num">${trending}</span><span class="stat-label">En Tendencia</span></div>
    `;
}


// ============================================================
// LOGIN (Formulario)
// ============================================================
function setupLoginForm() {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const username = document.getElementById("login-username").value;
            const password = document.getElementById("login-password").value;

            try {
                const response = await fetch(`${API_BASE}/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (response.ok) {
                    userToken = data.token;
                    // VULN: token guardado en variable global (deberia ser HttpOnly cookie)
                    console.log("Login exitoso. Token:", userToken);  // SMELL: expone token en consola

                    // VULN: XSS - Insertar username sin escapar en innerHTML
                    document.getElementById("user-info").innerHTML =
                        `Bienvenido, <strong>${data.username}</strong> (${data.role})`;  // VULN: XSS
                    document.getElementById("login-section").style.display = "none";
                    document.getElementById("user-section").style.display = "block";
                } else {
                    document.getElementById("login-error").textContent = "Usuario o contrasena incorrectos.";
                }
            } catch (error) {
                console.error("Error en login:", error);
            }
        });
    }
}


function setupCommentForm() {
    // SMELL: Funcion vacia que no hace nada util, deberia eliminarse o implementarse
    console.log("Formulario de comentarios listo");  // SMELL: debug log
}


// ============================================================
// SMELL: Codigo Duplicado
// Esta funcion de formateo de fecha es identica a la logica del backend.
// ============================================================
function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// SMELL: Funcion duplicada con nombre diferente pero misma logica que formatDate
function getFormattedDate(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${day}/${month}/${year} ${hours}:${minutes}`;
}
