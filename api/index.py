# ==============================================================
# API REST EN PYTHON - LICORERA DONDE JEFER (CON CONTROL DE ROLES)
# ==============================================================
# Sistema de Autorización Basado en Roles (RBAC):
# 1. Administrador (Jefer): Vender + Crear/Editar/Eliminar licores.
# 2. Vendedor (Carlos): Solo vender (registra pedido y descuenta stock).
# ==============================================================

import os
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import urllib.request
import urllib.error

app = FastAPI(
    title="API Licorera Donde Jefer",
    description="Servicios backend con autenticación y control de inventario",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_ANON_KEY", "")

# --------------------------------------------------------------
# MODELOS DE DATOS (PYDANTIC)
# --------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class ProductoBase(BaseModel):
    nombre: str
    categoria: str
    precio: float
    stock: int = 10
    imagen_url: Optional[str] = ""
    descripcion: Optional[str] = ""
    grado_alcohol: Optional[float] = 29.0
    volumen: Optional[str] = "750 ml"

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    precio: Optional[float] = None
    stock: Optional[int] = None
    imagen_url: Optional[str] = None
    descripcion: Optional[str] = None
    grado_alcohol: Optional[float] = None
    volumen: Optional[str] = None

class ItemPedido(BaseModel):
    producto_id: int
    producto_nombre: str
    cantidad: int
    precio_unitario: float

class PedidoCreate(BaseModel):
    cliente_nombre: str
    cliente_telefono: str
    cliente_direccion: str
    items: List[ItemPedido]
    total: float

# Usuarios en memoria
USUARIOS_DB = {
    "jefer": {"password": "admin123", "nombre": "Jefer (Administrador)", "rol": "administrador"},
    "vendedor": {"password": "vendedor123", "nombre": "Carlos (Vendedor)", "rol": "vendedor"}
}

PRODUCTOS_DEMO = [
    {"id": 1, "nombre": "Aguardiente Antioqueño Tapa Azul (Sin Azúcar)", "categoria": "Aguardiente", "precio": 48000.0, "stock": 35, "imagen_url": "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500", "descripcion": "El clásico paisa sin azúcar, suave al paladar.", "grado_alcohol": 29.0, "volumen": "750 ml"},
    {"id": 2, "nombre": "Aguardiente Antioqueño Tapa Roja (Tradicional)", "categoria": "Aguardiente", "precio": 46000.0, "stock": 28, "imagen_url": "https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500", "descripcion": "El tradicional anisado paisa con cuerpo.", "grado_alcohol": 29.0, "volumen": "750 ml"},
    {"id": 3, "nombre": "Ron Medellín Extra Añejo 8 Años", "categoria": "Ron", "precio": 78000.0, "stock": 20, "imagen_url": "https://images.unsplash.com/photo-1608885823108-25b4458d9297?w=500", "descripcion": "Madurado pacientemente en roble americano.", "grado_alcohol": 35.0, "volumen": "750 ml"},
    {"id": 4, "nombre": "Whisky Buchanan's DeLuxe 12 Años", "categoria": "Whisky", "precio": 145000.0, "stock": 25, "imagen_url": "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500", "descripcion": "Blended Scotch Whisky suave y frutal.", "grado_alcohol": 40.0, "volumen": "750 ml"},
    {"id": 5, "nombre": "Whisky Old Parr 12 Años", "categoria": "Whisky", "precio": 155000.0, "stock": 18, "imagen_url": "https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500", "descripcion": "La legendaria botella craquelada.", "grado_alcohol": 40.0, "volumen": "750 ml"},
    {"id": 6, "nombre": "Six Pack Cerveza Club Colombia Dorada", "categoria": "Cervezas", "precio": 28000.0, "stock": 50, "imagen_url": "https://images.unsplash.com/photo-1608270546114-1f6305a2e584?w=500", "descripcion": "Cerveza tipo lager dorada y lupulada.", "grado_alcohol": 4.7, "volumen": "Six Pack 330ml"},
    {"id": 7, "nombre": "Six Pack Cerveza Corona Extra", "categoria": "Cervezas", "precio": 36000.0, "stock": 40, "imagen_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500", "descripcion": "Cerveza clara mexicana para tomar helada.", "grado_alcohol": 4.5, "volumen": "Six Pack 355ml"},
    {"id": 8, "nombre": "Tequila Don Julio Blanco", "categoria": "Tequila", "precio": 260000.0, "stock": 12, "imagen_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500", "descripcion": "100% Agave Azul limpio y suave.", "grado_alcohol": 38.0, "volumen": "750 ml"}
]

PEDIDOS_DEMO = []

def supabase_request(endpoint: str, method: str = "GET", data: dict = None, headers_extra: dict = None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    if headers_extra:
        headers.update(headers_extra)
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except Exception as e:
        print(f"[Supabase Error]: {e}")
        return None

# ----------------- LOGIN ENDPOINT -----------------
@app.post("/api/auth/login")
def login(cred: LoginRequest):
    """Valida usuario y contraseña y devuelve el rol asignado."""
    u = cred.username.strip().lower()
    if u in USUARIOS_DB and USUARIOS_DB[u]["password"] == cred.password:
        return {
            "mensaje": f"Bienvenido {USUARIOS_DB[u]['nombre']}",
            "usuario": {
                "username": u,
                "nombre": USUARIOS_DB[u]["nombre"],
                "rol": USUARIOS_DB[u]["rol"]
            }
        }
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

# ----------------- PRODUCTOS (GET: Público) -----------------
@app.get("/api/products")
def obtener_productos(categoria: Optional[str] = None, q: Optional[str] = None):
    res = PRODUCTOS_DEMO
    if categoria and categoria.lower() != "todos":
        res = [p for p in res if p["categoria"].lower() == categoria.lower()]
    if q:
        res = [p for p in res if q.lower() in p["nombre"].lower()]
    return {"origen": "python_api", "data": res}

# ----------------- REGISTRAR VENTA (POST: Vendedor o Admin) -----------------
@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
def registrar_pedido(pedido: PedidoCreate, x_user_role: Optional[str] = Header(None)):
    """
    Solo permitido para Vendedor o Administrador.
    Valida stock y lo descuenta automáticamente del inventario.
    """
    if x_user_role not in ["vendedor", "administrador"]:
        raise HTTPException(status_code=403, detail="Debes identificarte como Vendedor o Administrador para despachar pedidos")

    # 1. Validar stock
    for item in pedido.items:
        prod = next((p for p in PRODUCTOS_DEMO if p["id"] == item.producto_id), None)
        if not prod:
            raise HTTPException(status_code=400, detail=f"El producto con ID {item.producto_id} no existe")
        if prod["stock"] < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para '{prod['nombre']}'. Disponible: {prod['stock']}")

    # 2. Descontar stock (Venta realizada)
    for item in pedido.items:
        for prod in PRODUCTOS_DEMO:
            if prod["id"] == item.producto_id:
                prod["stock"] -= item.cantidad

    nuevo_id = len(PEDIDOS_DEMO) + 1
    registro = pedido.model_dump()
    registro["id"] = nuevo_id
    registro["estado"] = "despachado"
    PEDIDOS_DEMO.append(registro)

    return {"mensaje": "¡Venta registrada y stock descontado con éxito!", "pedido_id": nuevo_id, "total": pedido.total}

# ----------------- CREAR LICOR (POST: Solo Administrador) -----------------
@app.post("/api/products", status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoBase, x_user_role: Optional[str] = Header(None)):
    if x_user_role != "administrador":
        raise HTTPException(status_code=403, detail="Permiso denegado: Solo el Administrador puede ingresar nuevos licores")

    nuevo_dict = producto.model_dump()
    nuevo_id = max([p["id"] for p in PRODUCTOS_DEMO], default=0) + 1
    nuevo_dict["id"] = nuevo_id
    PRODUCTOS_DEMO.append(nuevo_dict)
    return {"mensaje": "Licor creado con éxito por el Administrador", "producto": nuevo_dict}

# ----------------- ACTUALIZAR LICOR (PUT: Solo Administrador) -----------------
@app.put("/api/products/{producto_id}")
def actualizar_producto(producto_id: int, datos: ProductoUpdate, x_user_role: Optional[str] = Header(None)):
    if x_user_role != "administrador":
        raise HTTPException(status_code=403, detail="Permiso denegado: Solo el Administrador puede modificar inventario")

    actualizaciones = {k: v for k, v in datos.model_dump().items() if v is not None}
    for p in PRODUCTOS_DEMO:
        if p["id"] == producto_id:
            p.update(actualizaciones)
            return {"mensaje": "Licor actualizado por Administrador", "producto": p}
    raise HTTPException(status_code=404, detail="Licor no encontrado")

# ----------------- ELIMINAR LICOR (DELETE: Solo Administrador) -----------------
@app.delete("/api/products/{producto_id}")
def eliminar_producto(producto_id: int, x_user_role: Optional[str] = Header(None)):
    if x_user_role != "administrador":
        raise HTTPException(status_code=403, detail="Permiso denegado: Solo el Administrador puede eliminar referencias")

    global PRODUCTOS_DEMO
    ini_len = len(PRODUCTOS_DEMO)
    PRODUCTOS_DEMO = [p for p in PRODUCTOS_DEMO if p["id"] != producto_id]
    if len(PRODUCTOS_DEMO) < ini_len:
        return {"mensaje": f"Licor {producto_id} eliminado exitosamente"}
    raise HTTPException(status_code=404, detail="Licor no encontrado")
