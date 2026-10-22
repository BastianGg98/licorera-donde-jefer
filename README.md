# 🍾 Licorera Donde Jefer - Sistema Web Fullstack

¡Bienvenido al sistema oficial de **Licorera Donde Jefer**!
Un proyecto fullstack moderno con base de datos en **Supabase**, API de servicios en **Python** y un Frontend con tendencias visuales **Dark Luxury Glassmorphism**.

---

## 🏗️ Arquitectura del Sistema (Explicada fácil)

* **`database/schema.sql` (La Bodega en Supabase):**  
  Tablas para licores, categorías, clientes y ventas. Incluye el catálogo inicial con Aguardiente Antioqueño, Ron Medellín, Whisky Buchanan's, Cervezas heladas y Tequilas.
* **`api/index.py` (El Cantinero / API en Python):**  
  Implementa todos los métodos HTTP que pediste:
  * `GET /api/products`: Consultar licores con filtros de categoría y buscador.
  * `POST /api/products`: Agregar nuevos licores al inventario.
  * `PUT /api/products/{id}`: Modificar precios o stock.
  * `DELETE /api/products/{id}`: Eliminar licores.
  * `POST /api/orders`: Registrar ventas y pedidos de clientes.
* **`public/` (La Barra y la Vitrina / Frontend):**  
  * `index.html`: Estructura semántica, buscador en vivo y modales.
  * `styles.css`: Estilo oscuro moderno, vidrios esmerilados (Glassmorphism), acentos de neón ámbar y 100% responsivo para celulares.
  * `app.js`: Carrito interactivo con persistencia local (`localStorage`), consumo asíncrono (`fetch`) y panel de administración en vivo.
* **`servidor_local.py`:**  
  Servidor listo para correr en tu computador con un solo comando sin instalaciones pesadas.
* **`vercel.json`:**  
  Configuración para desplegar el proyecto completo en Vercel a través de GitHub.

---

## 🚀 Cómo Probarlo en Tu Computador (Paso a Paso)

1. Abre tu terminal de PowerShell en esta carpeta:
   ```bash
   cd C:\Users\jgarcia\Aprendiendo_Python\Licorera_Donde_Jefer
   ```
2. Inicia el servidor local:
   ```bash
   python servidor_local.py
   ```
3. Abre tu navegador favorito y entra a:
   👉 **http://localhost:8000**

¡Listo! Ya puedes ver la tienda, agregar licores al carrito, hacer pedidos y probar el panel de administración (Inventario).

---

## 🗄️ Cómo Conectar Supabase en 2 Minutos

1. Entra a tu proyecto en [Supabase Dashboard](https://supabase.com/dashboard).
2. Ve a la pestaña **SQL Editor** en el menú de la izquierda.
3. Abre el archivo `database/schema.sql`, copia todo su contenido y pégalo en el editor de Supabase.
4. Dale al botón **Run**. ¡En un segundo tendrás todas las tablas creadas con los licores cargados!
5. Ve a **Project Settings -> API** en Supabase y copia:
   * **Project URL**
   * **anon public key**
6. Agrégalas en Vercel como variables de entorno (`SUPABASE_URL` y `SUPABASE_KEY`) o en tu archivo `.env`.
