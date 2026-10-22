# ==============================================================
# API REST EN PYTHON - LICORERA DONDE JEFER (100% SUPABASE)
# ==============================================================
# CERO DATOS QUEMADOS EN MEMORIA:
# Todas las consultas, autenticación, ventas y modificaciones
# se ejecutan en tiempo real contra la base de datos de Supabase.
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
    description="Servicios backend conectados directamente a Supabase",
    version="3.0.0"
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

# --------------------------------------------------------------
# COMUNICACIÓN EXCLUSIVA CON SUPABASE (POSTGREST)
# --------------------------------------------------------------
def supabase_db(endpoint: str, method: str = "GET", data: dict = None, headers_extra: dict = None):
    """Ejecuta operaciones contra la base de datos de Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Credenciales de Supabase no configuradas en el servidor")

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
            return json.loads(body) if body else []
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"[Error Supabase {e.code}]: {error_msg}")
        raise HTTPException(status_code=e.code, detail=f"Error en Supabase: {error_msg}")
    except Exception as e:
        print(f"[Error Conexión Supabase]: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo de conexión con Supabase: {str(e)}")

# --------------------------------------------------------------
# ENDPOINTS 100% BASE DE DATOS
# --------------------------------------------------------------

@app.get("/api/health")
def estado_salud():
    """Verifica que el servicio esté conectado a Supabase."""
    return {
        "status": "online",
        "negocio": "Licorera Donde Jefer",
        "datos_en_memoria": "ELIMINADOS - 100% Supabase",
        "supabase_url": SUPABASE_URL
    }

# ----------------- LOGIN (Valida en tabla 'usuarios') -----------------
@app.post("/api/auth/login")
def login(cred: LoginRequest):
    """Valida usuario y contraseña directamente en la tabla usuarios de Supabase."""
    u = cred.username.strip().lower()
    p = cred.password.strip()

    # Consulta en Supabase
    resultado = supabase_db(f"usuarios?username=eq.{u}&password_hash=eq.{p}&select=id,username,nombre_completo,rol,activo", method="GET")
    if not resultado:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    usuario = resultado[0]
    if not usuario.get("activo", True):
        raise HTTPException(status_code=403, detail="Este usuario se encuentra inactivo")

    return {
        "mensaje": f"Bienvenido a la barra, {usuario['nombre_completo']}!",
        "usuario": {
            "username": usuario["username"],
            "nombre": usuario["nombre_completo"],
            "rol": usuario["rol"]
        }
    }

# ----------------- PRODUCTOS (GET: Consulta en tabla 'productos') -----------------
@app.get("/api/products")
def obtener_productos(categoria: Optional[str] = None, q: Optional[str] = None):
    """Consulta los licores directamente de la base de datos de Supabase."""
    query_params = ["order=id.asc"]
    if categoria and categoria.lower() != "todos":
        query_params.append(f"categoria=eq.{categoria}")
    if q:
        query_params.append(f"nombre=ilike.*{q}*")

    endpoint = "productos?select=*"
    if query_params:
        endpoint += "&" + "&".join(query_params)

    productos = supabase_db(endpoint, method="GET")
    return {"origen": "supabase_database", "data": productos}

@app.get("/api/products/{producto_id}")
def obtener_producto_por_id(producto_id: int):
    """Busca un licor por ID en Supabase."""
    resultado = supabase_db(f"productos?id=eq.{producto_id}&select=*", method="GET")
    if not resultado:
        raise HTTPException(status_code=404, detail="Licor no encontrado en Supabase")
    return resultado[0]

# ----------------- REGISTRAR VENTA (POST: Resta stock en Supabase) -----------------
@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
def registrar_pedido(pedido: PedidoCreate, x_user_role: Optional[str] = Header(None)):
    """
    Registra la venta en Supabase y resta el stock en la tabla productos.
    Requiere rol vendedor o administrador.
    """
    if x_user_role not in ["vendedor", "administrador"]:
        raise HTTPException(status_code=403, detail="Debes identificarte como Vendedor o Administrador para registrar ventas")

    if not pedido.items:
        raise HTTPException(status_code=400, detail="El pedido no contiene licores")

    # 1. Validar existencias actuales en Supabase
    productos_en_db = {}
    for item in pedido.items:
        res = supabase_db(f"productos?id=eq.{item.producto_id}&select=id,nombre,stock,precio", method="GET")
        if not res:
            raise HTTPException(status_code=404, detail=f"El licor {item.producto_nombre} no existe en la bodega")
        prod = res[0]
        if prod["stock"] < item.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para '{prod['nombre']}'. Disponible en bodega: {prod['stock']}, solicitado: {item.cantidad}"
            )
        productos_en_db[item.producto_id] = prod

    # 2. Descontar stock en Supabase para cada licor
    for item in pedido.items:
        nuevo_stock = productos_en_db[item.producto_id]["stock"] - item.cantidad
        supabase_db(f"productos?id=eq.{item.producto_id}", method="PATCH", data={"stock": nuevo_stock})

    # 3. Registrar venta en tabla 'pedidos'
    pedido_data = {
        "cliente_nombre": pedido.cliente_nombre,
        "cliente_telefono": pedido.cliente_telefono,
        "cliente_direccion": pedido.cliente_direccion,
        "total": pedido.total,
        "vendedor_username": x_user_role,
        "estado": "despachado"
    }
    nuevo_pedido = supabase_db("pedidos", method="POST", data=pedido_data)
    pedido_id = nuevo_pedido[0]["id"] if nuevo_pedido else None

    # 4. Registrar detalle en tabla 'detalle_pedidos'
    if pedido_id:
        for item in pedido.items:
            detalle = {
                "pedido_id": pedido_id,
                "producto_id": item.producto_id,
                "producto_nombre": item.producto_nombre,
                "cantidad": item.cantidad,
                "precio_unitario": item.precio_unitario,
                "subtotal": item.cantidad * item.precio_unitario
            }
            supabase_db("detalle_pedidos", method="POST", data=detalle)

    return {
        "mensaje": "¡Venta registrada y stock descontado directamente en Supabase!",
        "pedido_id": pedido_id,
        "total": pedido.total
    }

# ----------------- CREAR PRODUCTO (POST: Inserta en Supabase) -----------------
@app.post("/api/products", status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoBase, x_user_role: Optional[str] = Header(None)):
    """Solo Administrador: Inserta un licor en la tabla 'productos'."""
    if x_user_role != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: Solo el Administrador puede ingresar licores")

    nuevo = supabase_db("productos", method="POST", data=producto.model_dump())
    return {"mensaje": "Licor creado en Supabase con éxito", "producto": nuevo[0]}

# ----------------- ACTUALIZAR PRODUCTO (PUT: Modifica en Supabase) -----------------
@app.put("/api/products/{producto_id}")
def actualizar_producto(producto_id: int, datos: ProductoUpdate, x_user_role: Optional[str] = Header(None)):
    """Solo Administrador: Actualiza en la tabla 'productos'."""
    if x_user_role != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: Solo el Administrador puede modificar inventario")

    actualizaciones = {k: v for k, v in datos.model_dump().items() if v is not None}
    if not actualizaciones:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    actualizado = supabase_db(f"productos?id=eq.{producto_id}", method="PATCH", data=actualizaciones)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Licor no encontrado en Supabase")
    return {"mensaje": "Licor actualizado en Supabase", "producto": actualizado[0]}

# ----------------- ELIMINAR PRODUCTO (DELETE: Borra de Supabase) -----------------
@app.delete("/api/products/{producto_id}")
def eliminar_producto(producto_id: int, x_user_role: Optional[str] = Header(None)):
    """Solo Administrador: Elimina de la tabla 'productos'."""
    if x_user_role != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: Solo el Administrador puede eliminar referencias")

    supabase_db(f"productos?id=eq.{producto_id}", method="DELETE")
    return {"mensaje": f"Licor con ID {producto_id} eliminado definitivamente de Supabase"}
