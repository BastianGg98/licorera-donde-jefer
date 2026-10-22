# ==============================================================
# SERVIDOR LOCAL DE DESARROLLO - LICORERA DONDE JEFER (100% SUPABASE)
# ==============================================================
# Este servidor lee directamente desde la base de datos de Supabase.
# Cero listas quemadas en memoria: todo vive en la nube.
# ==============================================================

import os
import json
import urllib.parse
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
ENV_FILE = os.path.join(BASE_DIR, ".env")

# 1. Cargar credenciales desde .env
SUPABASE_URL = ""
SUPABASE_KEY = ""

if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "SUPABASE_URL":
                    SUPABASE_URL = v.strip().rstrip("/")
                elif k.strip() in ["SUPABASE_KEY", "SUPABASE_ANON_KEY"]:
                    SUPABASE_KEY = v.strip()

# Helper para comunicarse con Supabase
def call_supabase(endpoint, method="GET", data=None, headers_extra=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"error": "Credenciales de Supabase no configuradas en .env"}, 500

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
            return (json.loads(body) if body else []), resp.status
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[Supabase Error {e.code}]: {err_msg}")
        return {"error": err_msg}, e.code
    except Exception as e:
        print(f"[Supabase Conn Error]: {e}")
        return {"error": str(e)}, 500

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

        if parsed.path == "/api/health":
            return self._responder_json({
                "status": "online",
                "negocio": "Licorera Donde Jefer",
                "fuente_datos": "100% Supabase Cloud",
                "supabase_url": SUPABASE_URL
            })

        # GET /api/products -> Consulta en Supabase
        if parsed.path == "/api/products":
            params = urllib.parse.parse_qs(parsed.query)
            cat = params.get("categoria", [None])[0]
            q = params.get("q", [None])[0]

            query_parts = ["order=id.asc"]
            if cat and cat.lower() != "todos":
                query_parts.append(f"categoria=eq.{urllib.parse.quote(cat)}")
            if q:
                query_parts.append(f"nombre=ilike.*{urllib.parse.quote(q)}*")

            endpoint = "productos?select=*"
            if query_parts:
                endpoint += "&" + "&".join(query_parts)

            res, status_code = call_supabase(endpoint, method="GET")
            if status_code >= 400:
                return self._responder_json(res, status_code)
            return self._responder_json({"origen": "supabase_database", "data": res})

        # GET /api/orders -> Consulta en Supabase
        if parsed.path == "/api/orders":
            res, status_code = call_supabase("pedidos?select=*,detalle_pedidos(*)", method="GET")
            return self._responder_json(res, status_code)

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        payload = json.loads(body) if body else {}

        # ----------------- LOGIN (Valida en tabla 'usuarios' de Supabase) -----------------
        if parsed.path == "/api/auth/login":
            user = payload.get("username", "").strip().lower()
            password = payload.get("password", "").strip()

            endpoint = f"usuarios?username=eq.{urllib.parse.quote(user)}&password_hash=eq.{urllib.parse.quote(password)}&select=id,username,nombre_completo,rol,activo"
            res, status_code = call_supabase(endpoint, method="GET")

            if status_code == 200 and isinstance(res, list) and len(res) > 0:
                u = res[0]
                if not u.get("activo", True):
                    return self._responder_json({"error": "Usuario inactivo"}, 403)
                return self._responder_json({
                    "mensaje": f"Bienvenido, {u['nombre_completo']}!",
                    "usuario": {
                        "username": u["username"],
                        "nombre": u["nombre_completo"],
                        "rol": u["rol"]
                    }
                })
            return self._responder_json({"error": "Usuario o contrasena incorrectos en Supabase"}, 401)

        # ----------------- REGISTRAR VENTA (Resta stock en Supabase) -----------------
        if parsed.path == "/api/orders":
            rol_solicitante = self.headers.get("X-User-Role") or payload.get("rol_solicitante")
            if rol_solicitante not in ["vendedor", "administrador"]:
                return self._responder_json({"error": "Debes identificarte como Vendedor o Administrador para registrar ventas"}, 403)

            items = payload.get("items", [])
            if not items:
                return self._responder_json({"error": "El pedido no contiene licores"}, 400)

            # 1. Validar y descontar stock directamente en Supabase
            for item in items:
                p_id = item["producto_id"]
                cant = item["cantidad"]
                # Consultar stock actual
                prod_res, s_code = call_supabase(f"productos?id=eq.{p_id}&select=id,nombre,stock", method="GET")
                if not prod_res or s_code != 200:
                    return self._responder_json({"error": f"El licor {item.get('producto_nombre', p_id)} no existe en Supabase"}, 404)
                prod = prod_res[0]
                if prod["stock"] < cant:
                    return self._responder_json({
                        "error": f"Stock insuficiente en bodega para '{prod['nombre']}'. Disponible: {prod['stock']}, pedido: {cant}"
                    }, 400)

                # Descontar stock en Supabase
                nuevo_stock = prod["stock"] - cant
                call_supabase(f"productos?id=eq.{p_id}", method="PATCH", data={"stock": nuevo_stock})
                print(f">> [SUPABASE VENTA]: Stock de '{prod['nombre']}' actualizado a {nuevo_stock}")

            # 2. Guardar pedido en Supabase
            pedido_data = {
                "cliente_nombre": payload.get("cliente_nombre"),
                "cliente_telefono": payload.get("cliente_telefono"),
                "cliente_direccion": payload.get("cliente_direccion"),
                "total": payload.get("total"),
                "vendedor_username": rol_solicitante,
                "estado": "despachado"
            }
            res_ped, s_code = call_supabase("pedidos", method="POST", data=pedido_data)
            pedido_id = res_ped[0]["id"] if res_ped else None

            # 3. Guardar detalle de pedido en Supabase
            if pedido_id:
                for item in items:
                    det = {
                        "pedido_id": pedido_id,
                        "producto_id": item["producto_id"],
                        "producto_nombre": item["producto_nombre"],
                        "cantidad": item["cantidad"],
                        "precio_unitario": item["precio_unitario"],
                        "subtotal": item["cantidad"] * item["precio_unitario"]
                    }
                    call_supabase("detalle_pedidos", method="POST", data=det)

            return self._responder_json({
                "mensaje": "¡Venta registrada y stock descontado con exito en Supabase!",
                "pedido_id": pedido_id,
                "total": payload.get("total")
            }, 201)

        # ----------------- CREAR PRODUCTO (Solo Administrador en Supabase) -----------------
        if parsed.path == "/api/products":
            rol_solicitante = self.headers.get("X-User-Role") or payload.get("rol_solicitante")
            if rol_solicitante != "administrador":
                return self._responder_json({"error": "Acceso denegado: Solo el Administrador puede ingresar licores"}, 403)

            payload.pop("rol_solicitante", None)
            res, status_code = call_supabase("productos", method="POST", data=payload)
            return self._responder_json({"mensaje": "Licor creado en Supabase", "producto": res}, 201)

        self._responder_json({"error": "Ruta no encontrada"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/products/"):
            try:
                rol_solicitante = self.headers.get("X-User-Role")
                if rol_solicitante != "administrador":
                    return self._responder_json({"error": "Acceso denegado: Solo el Administrador puede modificar inventario"}, 403)

                prod_id = int(parsed.path.split("/")[-1])
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                datos = json.loads(body) if body else {}
                datos.pop("rol_solicitante", None)

                res, status_code = call_supabase(f"productos?id=eq.{prod_id}", method="PATCH", data=datos)
                return self._responder_json({"mensaje": "Licor actualizado en Supabase", "producto": res})
            except Exception as e:
                return self._responder_json({"error": str(e)}, 400)

        self._responder_json({"error": "No encontrado"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/products/"):
            try:
                rol_solicitante = self.headers.get("X-User-Role")
                if rol_solicitante != "administrador":
                    return self._responder_json({"error": "Acceso denegado: Solo el Administrador puede eliminar referencias"}, 403)

                prod_id = int(parsed.path.split("/")[-1])
                res, status_code = call_supabase(f"productos?id=eq.{prod_id}", method="DELETE")
                return self._responder_json({"mensaje": f"Licor {prod_id} eliminado de Supabase"})
            except Exception as e:
                return self._responder_json({"error": str(e)}, 400)

        self._responder_json({"error": "No encontrado"}, 404)

if __name__ == "__main__":
    print("=" * 65)
    print(">> LICORERA DONDE JEFER - 100% CONECTADO A SUPABASE <<")
    print(f">> Base de Datos: {SUPABASE_URL}")
    print(f">> Servidor Local: http://localhost:{PORT}")
    print(">> Usuarios reales en Supabase:")
    print("   - Administrador: jefer / admin123")
    print("   - Vendedor:      vendedor / vendedor123")
    print("=" * 65)
    server = HTTPServer(("0.0.0.0", PORT), LicoreraHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Servidor detenido.")
