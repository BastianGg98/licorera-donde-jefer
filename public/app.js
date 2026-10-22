// ==============================================================
// LICORERA DONDE JEFER - CONTROLADOR JAVASCRIPT (FRONTEND)
// ==============================================================
// Incluye Sistema de Roles (RBAC):
// 1. Invitado: Navega y ve la vitrina.
// 2. Vendedor (Carlos): Despacha pedidos (resta inventario automáticamente).
// 3. Administrador (Jefer): Despacha pedidos + Administra inventario (CRUD).
// ==============================================================

// Estado global de la aplicación
let productos = [];
let carrito = JSON.parse(localStorage.getItem("jefer_carrito")) || [];
let usuarioActual = JSON.parse(localStorage.getItem("jefer_usuario")) || null;
let categoriaActiva = "Todos";
let terminoBusqueda = "";

const API_BASE = "/api";

// --------------------------------------------------------------
// 1. INICIALIZACIÓN AL CARGAR LA PÁGINA
// --------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    aplicarEstadoAutenticacionUI();
    cargarProductosDesdeAPI();
    verificarEstadoBackend();
    configurarEventosUI();
    actualizarCarritoUI();
});

// --------------------------------------------------------------
// 2. SISTEMA DE AUTENTICACIÓN Y ROLES (RBAC)
// --------------------------------------------------------------
async function iniciarSesion(username, password) {
    try {
        const resp = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await resp.json();
        if (!resp.ok) {
            mostrarToast(data.error || "Credenciales incorrectas", "warning");
            return;
        }

        usuarioActual = data.usuario;
        localStorage.setItem("jefer_usuario", JSON.stringify(usuarioActual));

        // Cerrar modal de login
        document.getElementById("login-modal").classList.remove("active");
        document.getElementById("form-login").reset();

        aplicarEstadoAutenticacionUI();
        mostrarToast(`¡Bienvenido ${usuarioActual.nombre}! Sesión iniciada con éxito.`, "success");

    } catch (e) {
        console.error("Error en login:", e);
        mostrarToast("No se pudo conectar con el servicio de autenticación", "warning");
    }
}

function cerrarSesion() {
    usuarioActual = null;
    localStorage.removeItem("jefer_usuario");
    aplicarEstadoAutenticacionUI();
    mostrarToast("Has cerrado sesión. Modo invitado activado.", "info");
}

function autocompletarLogin(u, p) {
    document.getElementById("login-username").value = u;
    document.getElementById("login-password").value = p;
    iniciarSesion(u, p);
}

function aplicarEstadoAutenticacionUI() {
    const btnLoginTrigger = document.getElementById("btn-abrir-login");
    const userPill = document.getElementById("user-pill");
    const navUserRole = document.getElementById("nav-user-role");
    const navUserName = document.getElementById("nav-user-name");
    const btnAdmin = document.getElementById("btn-abrir-admin");
    const banner = document.getElementById("session-banner");
    const bannerTitle = document.getElementById("session-banner-title");
    const bannerDesc = document.getElementById("session-banner-desc");
    const bannerBtn = document.getElementById("banner-action-btn");
    const checkoutBadge = document.getElementById("checkout-user-badge");

    if (usuarioActual) {
        // Usuario logueado
        btnLoginTrigger.style.display = "none";
        userPill.style.display = "flex";
        navUserName.textContent = usuarioActual.nombre.split(" ")[0];

        if (usuarioActual.rol === "administrador") {
            navUserRole.className = "user-role-badge admin";
            navUserRole.textContent = "👑 Administrador";
            btnAdmin.style.display = "flex"; // Administrador PUEDE ver inventario
            bannerTitle.textContent = "Sesión Activa: Administrador (Jefer)";
            bannerDesc.textContent = "Tienes control total: gestionar catálogo, crear/borrar licores y despachar ventas.";
            bannerBtn.textContent = "Gestionar Inventario";
            bannerBtn.onclick = () => {
                renderizarAdminLista();
                document.getElementById("admin-modal").classList.add("active");
            };
        } else {
            navUserRole.className = "user-role-badge vendedor";
            navUserRole.textContent = "👤 Vendedor";
            btnAdmin.style.display = "none"; // Vendedor NO PUEDE ver administración de inventario
            bannerTitle.textContent = "Sesión Activa: Vendedor (Carlos)";
            bannerDesc.textContent = "Puedes adicionar ventas y despachar pedidos. El stock se descontará automáticamente.";
            bannerBtn.textContent = "Ver Pedido Actual";
            bannerBtn.onclick = () => {
                document.getElementById("cart-drawer").classList.add("active");
                document.getElementById("drawer-overlay").classList.add("active");
            };
        }

        if (checkoutBadge) {
            checkoutBadge.textContent = `${usuarioActual.nombre} (${usuarioActual.rol.toUpperCase()})`;
        }

    } else {
        // Modo Invitado (Sin autenticar)
        btnLoginTrigger.style.display = "flex";
        userPill.style.display = "none";
        btnAdmin.style.display = "none";

        bannerTitle.textContent = "Modo Invitado (Solo Lectura)";
        bannerDesc.textContent = "Inicia sesión como Vendedor o Administrador para despachar ventas o gestionar la bodega.";
        bannerBtn.textContent = "Iniciar Sesión";
        bannerBtn.onclick = () => document.getElementById("login-modal").classList.add("active");

        if (checkoutBadge) {
            checkoutBadge.textContent = "Invitado (Requiere Iniciar Sesión)";
        }
    }

    if (window.lucide) lucide.createIcons();
}

// --------------------------------------------------------------
// 3. CARGAR PRODUCTOS: MÉTODO GET
// --------------------------------------------------------------
async function cargarProductosDesdeAPI() {
    const grid = document.getElementById("products-grid");
    const countLabel = document.getElementById("products-count");

    grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-dim);">
            <p>Sirviendo los licores desde la bodega...</p>
        </div>
    `;

    try {
        let url = `${API_BASE}/products`;
        const params = new URLSearchParams();
        if (categoriaActiva !== "Todos") params.append("categoria", categoriaActiva);
        if (terminoBusqueda.trim()) params.append("q", terminoBusqueda.trim());

        if (params.toString()) url += `?${params.toString()}`;

        const respuesta = await fetch(url);
        if (!respuesta.ok) throw new Error("No se pudo conectar a la API");

        const resultado = await respuesta.json();
        productos = resultado.data || [];

        renderizarProductos(productos);
        countLabel.textContent = `${productos.length} licores listos para entrega`;

    } catch (error) {
        console.warn("[Aviso]: Usando catálogo local:", error);
        usarCatalogoDemoLocal();
    }
}

// --------------------------------------------------------------
// 4. RENDERIZAR PRODUCTOS
// --------------------------------------------------------------
function renderizarProductos(lista) {
    const grid = document.getElementById("products-grid");
    grid.innerHTML = "";

    if (lista.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--text-dim);">
                <i data-lucide="glass-water" style="width: 48px; height: 48px; margin-bottom: 12px; opacity: 0.5;"></i>
                <h4>No encontramos ese licor, parcero</h4>
                <p style="font-size: 0.9rem; margin-top: 6px;">Prueba buscando otra categoría o nombre.</p>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    lista.forEach(licor => {
        const card = document.createElement("article");
        card.className = "product-card glass-panel";

        const precioFormateado = new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            maximumFractionDigits: 0
        }).format(licor.precio);

        const agotado = licor.stock <= 0;

        card.innerHTML = `
            <div class="product-thumb-wrapper">
                <img src="${licor.imagen_url || 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500'}" alt="${licor.nombre}" class="product-thumb" loading="lazy">
                <span class="product-tag">${licor.categoria}</span>
            </div>
            <div class="product-info">
                <div class="product-meta">
                    <span>${licor.volumen || '750 ml'}</span>
                    •
                    <span>${licor.grado_alcohol || 29}% Alc.</span>
                    •
                    <span style="font-weight: 700; color: ${agotado ? 'var(--accent-red)' : (licor.stock <= 5 ? 'var(--primary-amber)' : 'var(--accent-green)')}">
                        ${agotado ? 'AGOTADO' : `Stock: ${licor.stock}`}
                    </span>
                </div>
                <h4 class="product-name">${licor.nombre}</h4>
                <p class="product-desc">${licor.descripcion || 'El mejor destilado seleccionado para tu fiesta.'}</p>
                <div class="product-bottom">
                    <div class="product-price-box">
                        <span class="price-label">Precio</span>
                        <span class="price-amount">${precioFormateado}</span>
                    </div>
                    <button class="btn-add-cart" onclick="agregarAlCarrito(${licor.id})" title="${agotado ? 'Sin existencias' : 'Añadir al pedido'}" ${agotado ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''}>
                        <i data-lucide="plus"></i>
                    </button>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });

    if (window.lucide) lucide.createIcons();
}

// --------------------------------------------------------------
// 5. CARRITO DE COMPRAS
// --------------------------------------------------------------
function agregarAlCarrito(productoId) {
    const licor = productos.find(p => p.id === productoId);
    if (!licor || licor.stock <= 0) {
        mostrarToast("Licor agotado por el momento", "warning");
        return;
    }

    const itemExistente = carrito.find(item => item.id === productoId);
    if (itemExistente) {
        if (itemExistente.cantidad < licor.stock) {
            itemExistente.cantidad++;
            mostrarToast(`Agregaste otra unidad de ${licor.nombre}`, "success");
        } else {
            mostrarToast(`Stock máximo disponible alcanzado (${licor.stock})`, "warning");
        }
    } else {
        carrito.push({
            id: licor.id,
            nombre: licor.nombre,
            precio: licor.precio,
            imagen_url: licor.imagen_url,
            cantidad: 1,
            stockMax: licor.stock
        });
        mostrarToast(`${licor.nombre} agregado al pedido 🍾`, "success");
    }

    guardarCarrito();
    actualizarCarritoUI();
}

function cambiarCantidad(productoId, cambio) {
    const item = carrito.find(i => i.id === productoId);
    if (!item) return;

    item.cantidad += cambio;
    if (item.cantidad <= 0) {
        carrito = carrito.filter(i => i.id !== productoId);
        mostrarToast("Producto eliminado del pedido", "info");
    }

    guardarCarrito();
    actualizarCarritoUI();
}

function guardarCarrito() {
    localStorage.setItem("jefer_carrito", JSON.stringify(carrito));
}

function actualizarCarritoUI() {
    const counter = document.getElementById("cart-counter");
    const navTotal = document.getElementById("cart-nav-total");
    const container = document.getElementById("cart-items-container");
    const subtotalEl = document.getElementById("summary-subtotal");
    const totalEl = document.getElementById("summary-total");

    const totalUnidades = carrito.reduce((acc, item) => acc + item.cantidad, 0);
    const totalDinero = carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);

    const formatoDinero = new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0
    }).format(totalDinero);

    counter.textContent = totalUnidades;
    navTotal.textContent = formatoDinero;
    subtotalEl.textContent = formatoDinero;
    totalEl.textContent = formatoDinero;

    if (carrito.length === 0) {
        container.innerHTML = `
            <div class="cart-empty-state">
                <i data-lucide="shopping-bag"></i>
                <p>Tu carrito está vacío, parcero.</p>
                <span style="font-size: 0.8rem;">¡Elige algo bueno pal fin de semana!</span>
            </div>
        `;
    } else {
        container.innerHTML = "";
        carrito.forEach(item => {
            const el = document.createElement("div");
            el.className = "cart-item";
            const subtotalItem = new Intl.NumberFormat("es-CO", {
                style: "currency",
                currency: "COP",
                maximumFractionDigits: 0
            }).format(item.precio * item.cantidad);

            el.innerHTML = `
                <img src="${item.imagen_url}" alt="${item.nombre}" class="cart-item-img">
                <div class="cart-item-details">
                    <h5 class="cart-item-name">${item.nombre}</h5>
                    <span class="cart-item-price">${subtotalItem}</span>
                </div>
                <div class="cart-item-controls">
                    <button class="cart-qty-btn" onclick="cambiarCantidad(${item.id}, -1)">-</button>
                    <span class="cart-qty-num">${item.cantidad}</span>
                    <button class="cart-qty-btn" onclick="cambiarCantidad(${item.id}, 1)">+</button>
                </div>
            `;
            container.appendChild(el);
        });
    }

    if (window.lucide) lucide.createIcons();
}

// --------------------------------------------------------------
// 6. REGISTRAR VENTA: MÉTODO POST CON DESCUENTO DE STOCK
// --------------------------------------------------------------
async function despacharPedido(nombre, telefono, direccion) {
    if (!usuarioActual) {
        mostrarToast("¡Pilas! Debes iniciar sesión como Vendedor o Administrador para registrar una venta.", "warning");
        document.getElementById("checkout-modal").classList.remove("active");
        document.getElementById("login-modal").classList.add("active");
        return;
    }

    if (carrito.length === 0) {
        mostrarToast("El pedido está vacío", "warning");
        return;
    }

    const total = carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);

    const payload = {
        cliente_nombre: nombre,
        cliente_telefono: telefono,
        cliente_direccion: direccion,
        total: total,
        rol_solicitante: usuarioActual.rol,
        vendedor: usuarioActual.username,
        items: carrito.map(item => ({
            producto_id: item.id,
            producto_nombre: item.nombre,
            cantidad: item.cantidad,
            precio_unitario: item.precio
        }))
    };

    try {
        const resp = await fetch(`${API_BASE}/orders`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-User-Role": usuarioActual.rol
            },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        if (!resp.ok) {
            mostrarToast(data.error || "No se pudo registrar la venta", "warning");
            return;
        }

        // Éxito: Limpiar carrito
        carrito = [];
        guardarCarrito();
        actualizarCarritoUI();

        // Cerrar modales
        document.getElementById("checkout-modal").classList.remove("active");
        document.getElementById("cart-drawer").classList.remove("active");
        document.getElementById("drawer-overlay").classList.remove("active");

        mostrarToast(`¡Venta registrada con éxito por ${usuarioActual.nombre}! Stock actualizado en bodega. 📦📉`, "success");

        // Recargar productos para ver el stock reducido en pantalla
        await cargarProductosDesdeAPI();

    } catch (e) {
        console.error("Error al registrar venta:", e);
        mostrarToast("Error enviando la venta", "warning");
    }
}

// --------------------------------------------------------------
// 7. GESTOR DE PRODUCTOS: EXCLUSIVO ADMINISTRADOR
// --------------------------------------------------------------
async function guardarProductoAdmin(e) {
    e.preventDefault();

    if (!usuarioActual || usuarioActual.rol !== "administrador") {
        mostrarToast("Acceso denegado: Solo el Administrador puede modificar licores", "warning");
        return;
    }

    const id = document.getElementById("admin-prod-id").value;
    const nombre = document.getElementById("admin-nombre").value;
    const categoria = document.getElementById("admin-categoria").value;
    const precio = parseFloat(document.getElementById("admin-precio").value);
    const stock = parseInt(document.getElementById("admin-stock").value);
    const grado = parseFloat(document.getElementById("admin-grado").value) || 29.0;
    const imagen = document.getElementById("admin-imagen").value || "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500";
    const descripcion = document.getElementById("admin-descripcion").value;

    const datos = {
        nombre,
        categoria,
        precio,
        stock,
        grado_alcohol: grado,
        imagen_url: imagen,
        descripcion,
        rol_solicitante: "administrador"
    };

    try {
        let resp;
        if (id) {
            resp = await fetch(`${API_BASE}/products/${id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-User-Role": "administrador"
                },
                body: JSON.stringify(datos)
            });
            mostrarToast("Licor actualizado con éxito en inventario (PUT) 🔄", "success");
        } else {
            resp = await fetch(`${API_BASE}/products`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-User-Role": "administrador"
                },
                body: JSON.stringify(datos)
            });
            mostrarToast("Nueva referencia agregada a la bodega (POST) ✨", "success");
        }

        const data = await resp.json();
        if (!resp.ok) {
            mostrarToast(data.error || "Error al guardar el licor", "warning");
            return;
        }

        document.getElementById("form-admin-producto").reset();
        document.getElementById("admin-prod-id").value = "";
        document.getElementById("admin-form-title").textContent = "Agregar Nuevo Licor (POST)";
        document.getElementById("btn-cancelar-admin").style.display = "none";

        await cargarProductosDesdeAPI();
        renderizarAdminLista();

    } catch (err) {
        console.error("Error guardando:", err);
        mostrarToast("Hubo un error al procesar el licor", "warning");
    }
}

async function eliminarProductoAdmin(id) {
    if (!usuarioActual || usuarioActual.rol !== "administrador") {
        mostrarToast("Acceso denegado: Solo el Administrador puede eliminar referencias", "warning");
        return;
    }

    if (!confirm("¿Seguro que deseas eliminar definitivamente este licor de la bodega?")) return;

    try {
        const resp = await fetch(`${API_BASE}/products/${id}`, {
            method: "DELETE",
            headers: {
                "X-User-Role": "administrador"
            }
        });

        const data = await resp.json();
        if (resp.ok) {
            mostrarToast("Referencia eliminada de la bodega (DELETE) 🗑️", "info");
            await cargarProductosDesdeAPI();
            renderizarAdminLista();
        } else {
            mostrarToast(data.error || "No se pudo eliminar", "warning");
        }
    } catch (err) {
        console.error("Error al eliminar:", err);
        mostrarToast("No se pudo eliminar el licor", "warning");
    }
}

function prepararEdicion(id) {
    const licor = productos.find(p => p.id === id);
    if (!licor) return;

    document.getElementById("admin-prod-id").value = licor.id;
    document.getElementById("admin-nombre").value = licor.nombre;
    document.getElementById("admin-categoria").value = licor.categoria;
    document.getElementById("admin-precio").value = licor.precio;
    document.getElementById("admin-stock").value = licor.stock;
    document.getElementById("admin-grado").value = licor.grado_alcohol || 29;
    document.getElementById("admin-imagen").value = licor.imagen_url || "";
    document.getElementById("admin-descripcion").value = licor.descripcion || "";

    document.getElementById("admin-form-title").textContent = `Editando: ${licor.nombre} (PUT)`;
    document.getElementById("btn-cancelar-admin").style.display = "inline-block";
}

function renderizarAdminLista() {
    const container = document.getElementById("admin-items-list");
    container.innerHTML = "";

    productos.forEach(p => {
        const div = document.createElement("div");
        div.className = "admin-item-card";
        div.innerHTML = `
            <div class="admin-item-info">
                <strong>${p.nombre}</strong>
                <span>${p.categoria} • $${p.precio.toLocaleString()} • Stock: ${p.stock}</span>
            </div>
            <div class="admin-item-actions">
                <button class="btn-icon-edit" onclick="prepararEdicion(${p.id})" title="Editar (PUT)">
                    <i data-lucide="edit-3"></i>
                </button>
                <button class="btn-icon-del" onclick="eliminarProductoAdmin(${p.id})" title="Eliminar (DELETE)">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        `;
        container.appendChild(div);
    });

    if (window.lucide) lucide.createIcons();
}

// --------------------------------------------------------------
// 8. EVENTOS DE INTERFAZ
// --------------------------------------------------------------
function configurarEventosUI() {
    // Filtros de categoría
    const pills = document.querySelectorAll(".category-pills .pill");
    pills.forEach(pill => {
        pill.addEventListener("click", () => {
            pills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            categoriaActiva = pill.getAttribute("data-categoria");
            document.getElementById("current-category-title").textContent = 
                categoriaActiva === "Todos" ? "Catálogo Completo" : `Categoría: ${categoriaActiva}`;
            cargarProductosDesdeAPI();
        });
    });

    // Buscador
    let timeoutBusqueda;
    const inputBusqueda = document.getElementById("input-busqueda");
    inputBusqueda.addEventListener("input", (e) => {
        clearTimeout(timeoutBusqueda);
        timeoutBusqueda = setTimeout(() => {
            terminoBusqueda = e.target.value;
            cargarProductosDesdeAPI();
        }, 300);
    });

    // Abrir/Cerrar Carrito
    const drawer = document.getElementById("cart-drawer");
    const overlay = document.getElementById("drawer-overlay");
    const btnAbrirCarrito = document.getElementById("btn-abrir-carrito");
    const btnCerrarCarrito = document.getElementById("btn-cerrar-carrito");

    btnAbrirCarrito.addEventListener("click", () => {
        drawer.classList.add("active");
        overlay.classList.add("active");
    });

    const cerrarCarrito = () => {
        drawer.classList.remove("active");
        overlay.classList.remove("active");
    };

    btnCerrarCarrito.addEventListener("click", cerrarCarrito);
    overlay.addEventListener("click", cerrarCarrito);

    // Modal Login
    const loginModal = document.getElementById("login-modal");
    document.getElementById("btn-abrir-login").addEventListener("click", () => {
        loginModal.classList.add("active");
    });
    document.getElementById("btn-cerrar-login").addEventListener("click", () => {
        loginModal.classList.remove("active");
    });
    document.getElementById("form-login").addEventListener("submit", (e) => {
        e.preventDefault();
        const u = document.getElementById("login-username").value;
        const p = document.getElementById("login-password").value;
        iniciarSesion(u, p);
    });
    document.getElementById("btn-logout").addEventListener("click", cerrarSesion);

    // Modal Checkout
    const checkoutModal = document.getElementById("checkout-modal");
    const btnIniciarCheckout = document.getElementById("btn-iniciar-checkout");
    const btnCerrarModal = document.getElementById("btn-cerrar-modal");

    btnIniciarCheckout.addEventListener("click", () => {
        if (!usuarioActual) {
            mostrarToast("Debes identificarte como Vendedor o Administrador para registrar la venta", "warning");
            loginModal.classList.add("active");
            return;
        }
        if (carrito.length === 0) {
            mostrarToast("Tu pedido está vacío", "warning");
            return;
        }
        const totalDinero = carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);
        document.getElementById("modal-total-display").textContent = 
            new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(totalDinero);
        checkoutModal.classList.add("active");
    });

    btnCerrarModal.addEventListener("click", () => checkoutModal.classList.remove("active"));

    document.getElementById("form-checkout").addEventListener("submit", (e) => {
        e.preventDefault();
        const nom = document.getElementById("checkout-nombre").value;
        const tel = document.getElementById("checkout-telefono").value;
        const dir = document.getElementById("checkout-direccion").value;
        despacharPedido(nom, tel, dir);
    });

    // Modal Admin
    const adminModal = document.getElementById("admin-modal");
    document.getElementById("btn-abrir-admin").addEventListener("click", () => {
        if (!usuarioActual || usuarioActual.rol !== "administrador") {
            mostrarToast("Solo el Administrador tiene acceso al inventario", "warning");
            return;
        }
        renderizarAdminLista();
        adminModal.classList.add("active");
    });
    document.getElementById("btn-cerrar-admin").addEventListener("click", () => {
        adminModal.classList.remove("active");
    });
    document.getElementById("form-admin-producto").addEventListener("submit", guardarProductoAdmin);
    document.getElementById("btn-cancelar-admin").addEventListener("click", () => {
        document.getElementById("form-admin-producto").reset();
        document.getElementById("admin-prod-id").value = "";
        document.getElementById("admin-form-title").textContent = "Agregar Nuevo Licor (POST)";
        document.getElementById("btn-cancelar-admin").style.display = "none";
    });
}

// --------------------------------------------------------------
// 9. TOASTS
// --------------------------------------------------------------
function mostrarToast(mensaje, tipo = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;

    let iconName = "info";
    if (tipo === "success") iconName = "check-circle";
    if (tipo === "warning") iconName = "alert-triangle";

    toast.innerHTML = `
        <i data-lucide="${iconName}"></i>
        <span>${mensaje}</span>
    `;

    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// --------------------------------------------------------------
// 10. VERIFICAR BACKEND
// --------------------------------------------------------------
async function verificarEstadoBackend() {
    const statusText = document.getElementById("backend-status-text");
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            statusText.textContent = "Servicio con Control de Roles • Activo";
        } else {
            statusText.textContent = "Modo Demostración";
        }
    } catch {
        statusText.textContent = "Catálogo Offline";
    }
}

// Catálogo demo de reserva
function usarCatalogoDemoLocal() {
    productos = [
        { id: 1, nombre: "Aguardiente Antioqueño Tapa Azul (Sin Azúcar)", categoria: "Aguardiente", precio: 48000, stock: 35, imagen_url: "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500", descripcion: "El clásico paisa sin azúcar, suave al paladar.", grado_alcohol: 29.0, volumen: "750 ml" },
        { id: 2, nombre: "Aguardiente Antioqueño Tapa Roja (Tradicional)", categoria: "Aguardiente", precio: 46000, stock: 28, imagen_url: "https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500", descripcion: "El tradicional anisado paisa con cuerpo.", grado_alcohol: 29.0, volumen: "750 ml" },
        { id: 3, nombre: "Ron Medellín Extra Añejo 8 Años", categoria: "Ron", precio: 78000, stock: 20, imagen_url: "https://images.unsplash.com/photo-1608885823108-25b4458d9297?w=500", descripcion: "Madurado pacientemente en roble americano.", grado_alcohol: 35.0, volumen: "750 ml" },
        { id: 4, nombre: "Whisky Buchanan's DeLuxe 12 Años", categoria: "Whisky", precio: 145000, stock: 25, imagen_url: "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500", descripcion: "Blended Scotch Whisky suave y frutal.", grado_alcohol: 40.0, volumen: "750 ml" },
        { id: 5, nombre: "Whisky Old Parr 12 Años", categoria: "Whisky", precio: 155000, stock: 18, imagen_url: "https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500", descripcion: "La legendaria botella craquelada.", grado_alcohol: 40.0, volumen: "750 ml" },
        { id: 6, nombre: "Six Pack Cerveza Club Colombia Dorada", categoria: "Cervezas", precio: 28000, stock: 50, imagen_url: "https://images.unsplash.com/photo-1608270546114-1f6305a2e584?w=500", descripcion: "Cerveza tipo lager dorada y lupulada.", grado_alcohol: 4.7, volumen: "Six Pack 330ml" },
        { id: 7, nombre: "Six Pack Cerveza Corona Extra", categoria: "Cervezas", precio: 36000, stock: 40, imagen_url: "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500", descripcion: "Cerveza clara mexicana para tomar helada.", grado_alcohol: 4.5, volumen: "Six Pack 355ml" },
        { id: 8, nombre: "Tequila Don Julio Blanco", categoria: "Tequila", precio: 260000, stock: 12, imagen_url: "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", descripcion: "100% Agave Azul limpio y suave.", grado_alcohol: 38.0, volumen: "750 ml" }
    ];

    let filtrados = productos;
    if (categoriaActiva !== "Todos") {
        filtrados = filtrados.filter(p => p.categoria.toLowerCase() === categoriaActiva.toLowerCase());
    }
    if (terminoBusqueda.trim()) {
        filtrados = filtrados.filter(p => p.nombre.toLowerCase().includes(terminoBusqueda.toLowerCase()));
    }
    renderizarProductos(filtrados);
    document.getElementById("products-count").textContent = `${filtrados.length} licores listos para entrega (Catálogo Demo)`;
}
