# ==============================================================
# SERVIDOR LOCAL DE DESARROLLO - LICORERA DONDE JEFER
# ==============================================================
# Incluye Autenticacion con Roles (RBAC):
# - Administrador (Jefer): Control total (vender + editar/borrar/crear licores)
# - Vendedor (Carlos): Solo vender (adiciona pedidos y resta stock)
# ==============================================================

import os
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# Usuarios preconfigurados en memoria para pruebas
USUARIOS = {
    "jefer": {
        "username": "jefer",
        "password": "admin123",
        "nombre": "Jefer (Administrador)",
        "rol": "administrador"
    },
    "vendedor": {
        "username": "vendedor",
        "password": "vendedor123",
        "nombre": "Carlos (Vendedor)",
        "rol": "vendedor"
    }
}

# Catalogo inicial con stock real en memoria
PRODUCTOS = [
    {
        "id": 1,
        "nombre": "Aguardiente Antioqueño Tapa Azul (Sin Azúcar)",
        "categoria": "Aguardiente",
        "precio": 48000,
        "stock": 35,
        "imagen_url": "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500&auto=format&fit=crop",
        "descripcion": "El clasico paisa sin azucar, suave al paladar y perfecto pal tinto o el remate.",
        "grado_alcohol": 29.0,
        "volumen": "750 ml"
    },
    {
        "id": 2,
        "nombre": "Aguardiente Antioqueño Tapa Roja (Tradicional)",
        "categoria": "Aguardiente",
        "precio": 46000,
        "stock": 28,
        "imagen_url": "https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500&auto=format&fit=crop",
        "descripcion": "El tradicional anisado paisa con cuerpo y sabor inconfundible de fiesta.",
        "grado_alcohol": 29.0,
        "volumen": "750 ml"
    },
    {
        "id": 3,
        "nombre": "Ron Medellín Extra Añejo 8 Años",
        "categoria": "Ron",
        "precio": 78000,
        "stock": 20,
        "imagen_url": "https://images.unsplash.com/photo-1608885823108-25b4458d9297?w=500&auto=format&fit=crop",
        "descripcion": "Madurado pacientemente en barricas de roble americano, sabor suave a caramelo.",
        "grado_alcohol": 35.0,
        "volumen": "750 ml"
    },
    {
        "id": 4,
        "nombre": "Whisky Buchanan's DeLuxe 12 Años",
        "categoria": "Whisky",
        "precio": 145000,
        "stock": 25,
        "imagen_url": "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500&auto=format&fit=crop",
        "descripcion": "Blended Scotch Whisky suave, con notas citricas y toques sutiles de turba.",
        "grado_alcohol": 40.0,
        "volumen": "750 ml"
    },
    {
        "id": 5,
        "nombre": "Whisky Old Parr 12 Años",
        "categoria": "Whisky",
        "precio": 155000,
        "stock": 18,
        "imagen_url": "https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500&auto=format&fit=crop",
        "descripcion": "La legendaria botella craquelada. Rico, afrutado y aterciopelado.",
        "grado_alcohol": 40.0,
        "volumen": "750 ml"
    },
    {
        "id": 6,
        "nombre": "Six Pack Cerveza Club Colombia Dorada",
        "categoria": "Cervezas",
        "precio": 28000,
        "stock": 50,
        "imagen_url": "https://images.unsplash.com/photo-1608270546114-1f6305a2e584?w=500&auto=format&fit=crop",
        "descripcion": "Cerveza tipo lager dorada brillante, con notas sutiles de lupulo y cebada.",
        "grado_alcohol": 4.7,
        "volumen": "Six Pack 330ml"
    },
    {
        "id": 7,
        "nombre": "Six Pack Cerveza Corona Extra",
        "categoria": "Cervezas",
        "precio": 36000,
        "stock": 40,
        "imagen_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&auto=format&fit=crop",
        "descripcion": "Cerveza clara mexicana para tomar bien helada con una rodaja de limon.",
        "grado_alcohol": 4.5,
        "volumen": "Six Pack 355ml"
    },
    {
        "id": 8,
        "nombre": "Tequila Don Julio Blanco",
        "categoria": "Tequila",
        "precio": 260000,
        "stock": 12,
        "imagen_url": "https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500&auto=format&fit=crop",
        "descripcion": "100% Agave Azul de Jalisco, con sabor limpio a citricos y notas de pimienta.",
        "grado_alcohol": 38.0,
        "volumen": "750 ml"
    }
]

PEDIDOS = []

class LicoreraHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def _responder_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # Endpoint de salud
        if parsed.path == "/api/health":
            return self._responder_json({
                "status": "online",
                "negocio": "Licorera Donde Jefer",
                "mensaje": "Servicio local activo con control de roles",
                "supabase_conectado": False
            })

        # Endpoint GET /api/products
        if parsed.path == "/api/products":
            params = urllib.parse.parse_qs(parsed.query)
            cat = params.get("categoria", [None])[0]
            q = params.get("q", [None])[0]

            resultado = PRODUCTOS
            if cat and cat.lower() != "todos":
                resultado = [p for p in resultado if p["categoria"].lower() == cat.lower()]
            if q:
                resultado = [p for p in resultado if q.lower() in p["nombre"].lower()]

            return self._responder_json({"origen": "local_python", "data": resultado})

        # Endpoint GET /api/orders
        if parsed.path == "/api/orders":
            return self._responder_json(PEDIDOS)

        # Si no es una ruta /api, sirve los archivos estaticos de public/
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        payload = json.loads(body) if body else {}

        # ----------------- LOGIN (AUTENTICACIÓN) -----------------
        if parsed.path == "/api/auth/login":
            user = payload.get("username", "").strip().lower()
            password = payload.get("password", "").strip()

            if user in USUARIOS and USUARIOS[user]["password"] == password:
                u_info = USUARIOS[user]
                return self._responder_json({
                    "mensaje": f"Bienvenido a la barra, {u_info['nombre']}!",
                    "usuario": {
                        "username": u_info["username"],
                        "nombre": u_info["nombre"],
                        "rol": u_info["rol"]
                    }
                })
            return self._responder_json({"error": "Usuario o contrasena incorrectos"}, 401)

        # ----------------- CREAR PRODUCTO (SOLO ADMIN) -----------------
        if parsed.path == "/api/products":
            rol_solicitante = self.headers.get("X-User-Role") or payload.get("rol_solicitante")
            if rol_solicitante != "administrador":
                return self._responder_json({"error": "Acceso denegado: Solo el Administrador puede ingresar referencias"}, 403)

            nuevo_id = max([p["id"] for p in PRODUCTOS], default=0) + 1
            payload["id"] = nuevo_id
            payload.pop("rol_solicitante", None)
            PRODUCTOS.append(payload)
            return self._responder_json({"mensaje": "Licor creado con exito", "producto": payload}, 201)

        # ----------------- REGISTRAR VENTA / PEDIDO (VENDEDOR O ADMIN) -----------------
        if parsed.path == "/api/orders":
            rol_solicitante = self.headers.get("X-User-Role") or payload.get("rol_solicitante")
            if rol_solicitante not in ["vendedor", "administrador"]:
                return self._responder_json({"error": "Debes iniciar sesion como Vendedor o Administrador para despachar pedidos"}, 401)

            items = payload.get("items", [])
            if not items:
                return self._responder_json({"error": "El pedido no contiene licores"}, 400)

            # 1. Validar que haya stock suficiente para cada licor
            for item in items:
                p_id = item["producto_id"]
                cant = item["cantidad"]
                licor = next((p for p in PRODUCTOS if p["id"] == p_id), None)
                if not licor:
                    return self._responder_json({"error": f"El licor {item.get('producto_nombre', p_id)} no existe"}, 400)
                if licor["stock"] < cant:
                    return self._responder_json({
                        "error": f"Stock insuficiente para '{licor['nombre']}'. Disponible: {licor['stock']}, solicitado: {cant}"
                    }, 400)

            # 2. Descontar del inventario (Stock = Stock - Cantidad)
            for item in items:
                p_id = item["producto_id"]
                cant = item["cantidad"]
                for p in PRODUCTOS:
                    if p["id"] == p_id:
                        p["stock"] -= cant
                        print(f">> [VENTA]: Descontadas {cant} unidades de '{p['nombre']}'. Stock restante: {p['stock']}")

            nuevo_id = len(PEDIDOS) + 1
            payload["id"] = nuevo_id
            payload["estado"] = "despachado"
            payload.pop("rol_solicitante", None)
            PEDIDOS.append(payload)

            return self._responder_json({
                "mensaje": "¡Venta registrada y stock actualizado con exito!",
                "pedido_id": nuevo_id,
                "total": payload.get("total")
            }, 201)

        self._responder_json({"error": "Ruta no encontrada"}, 404)

    def do_PUT(self):
        # ----------------- EDITAR PRODUCTO (SOLO ADMIN) -----------------
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/products/"):
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                datos = json.loads(body) if body else {}

                rol_solicitante = self.headers.get("X-User-Role") or datos.get("rol_solicitante")
                if rol_solicitante != "administrador":
                    return self._responder_json({"error": "Acceso denegado: Solo el Administrador puede editar el inventario"}, 403)

                prod_id = int(parsed.path.split("/")[-1])
                datos.pop("rol_solicitante", None)

                for p in PRODUCTOS:
                    if p["id"] == prod_id:
                        p.update(datos)
                        return self._responder_json({"mensaje": "Licor actualizado en inventario", "producto": p})
            except Exception as e:
                return self._responder_json({"error": str(e)}, 400)

        self._responder_json({"error": "No encontrado"}, 404)

    def do_DELETE(self):
        # ----------------- BORRAR PRODUCTO (SOLO ADMIN) -----------------
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/products/"):
            try:
                rol_solicitante = self.headers.get("X-User-Role")
                if rol_solicitante != "administrador":
                    return self._responder_json({"error": "Acceso denegado: Solo el Administrador puede eliminar licores"}, 403)

                prod_id = int(parsed.path.split("/")[-1])
                global PRODUCTOS
                ini_len = len(PRODUCTOS)
                PRODUCTOS = [p for p in PRODUCTOS if p["id"] != prod_id]
                if len(PRODUCTOS) < ini_len:
                    return self._responder_json({"mensaje": f"Licor con ID {prod_id} eliminado exitosamente"})
            except Exception as e:
                return self._responder_json({"error": str(e)}, 400)

        self._responder_json({"error": "No encontrado"}, 404)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), LicoreraHandler)
    print("=" * 65)
    print(">> LICORERA DONDE JEFER - SERVIDOR ACTIVO CON CONTROL DE ROLES <<")
    print(f">> Entra en tu navegador a: http://localhost:{PORT}")
    print(">> Credenciales de prueba:")
    print("   - Administrador: jefer / admin123")
    print("   - Vendedor:      vendedor / vendedor123")
    print("Presiona Ctrl + C en la terminal para apagar el servidor.")
    print("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Servidor detenido. Hasta la proxima, Jefer!")
