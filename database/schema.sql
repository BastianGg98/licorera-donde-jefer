-- ==============================================================
-- LICORERA DONDE JEFER - BASE DE DATOS (SUPABASE / POSTGRESQL)
-- ==============================================================
-- Este archivo contiene las instrucciones para crear las tablas
-- y poblar el catalogo inicial con los mejores licores de la casa,
-- ademas de la tabla de usuarios con roles (vendedor y administrador).
-- ==============================================================

-- 1. Tabla de Usuarios y Roles (RBAC: Role-Based Access Control)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('administrador', 'vendedor')),
    activo BOOLEAN DEFAULT true,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Tabla de Categorias
CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    icono VARCHAR(50) DEFAULT 'wine',
    descripcion TEXT
);

-- 3. Tabla de Productos (Licores con Control de Stock)
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    precio NUMERIC(12, 2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL DEFAULT 10 CHECK (stock >= 0),
    imagen_url TEXT,
    descripcion TEXT,
    grado_alcohol NUMERIC(4, 1),
    volumen VARCHAR(20) DEFAULT '750 ml',
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Tabla de Pedidos (Ventas registradas por vendedor/admin)
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    cliente_nombre VARCHAR(100) NOT NULL,
    cliente_telefono VARCHAR(30) NOT NULL,
    cliente_direccion TEXT NOT NULL,
    total NUMERIC(12, 2) NOT NULL,
    vendedor_username VARCHAR(50) DEFAULT 'sistema',
    estado VARCHAR(30) DEFAULT 'despachado',
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Detalle de los Pedidos
CREATE TABLE IF NOT EXISTS detalle_pedidos (
    id SERIAL PRIMARY KEY,
    pedido_id INT REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(id),
    producto_nombre VARCHAR(120) NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12, 2) NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL
);

-- ==============================================================
-- POBLAR USUARIOS INICIALES (ADMIN Y VENDEDOR)
-- ==============================================================
INSERT INTO usuarios (username, password_hash, nombre_completo, rol) VALUES
('jefer', 'admin123', 'Jefer (Dueño & Administrador)', 'administrador'),
('vendedor', 'vendedor123', 'Carlos (Vendedor de Barra)', 'vendedor')
ON CONFLICT (username) DO NOTHING;

-- ==============================================================
-- POBLAR CON DATOS INICIALES (CATALOGO DE DONDE JEFER)
-- ==============================================================
INSERT INTO categorias (nombre, icono, descripcion) VALUES
('Aguardiente', 'sparkles', 'El alma de la fiesta colombiana'),
('Ron', 'flame', 'Añejo, oscuro y con sabor a tradicion'),
('Whisky', 'gem', 'Elegancia, malta y destilados premium'),
('Cervezas', 'beer', 'Frias, refrescantes y de barril'),
('Tequila', 'zap', 'De puro agave para los mas valientes')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO productos (nombre, categoria, precio, stock, imagen_url, descripcion, grado_alcohol, volumen) VALUES
-- Aguardientes
('Aguardiente Antioqueño Tapa Azul (Sin Azúcar)', 'Aguardiente', 48000, 35, 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500&auto=format&fit=crop', 'El clasico paisa sin azucar, suave al paladar y perfecto pal tinto o el remate.', 29.0, '750 ml'),
('Aguardiente Antioqueño Tapa Roja (Tradicional)', 'Aguardiente', 46000, 28, 'https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500&auto=format&fit=crop', 'El tradicional anisado paisa con cuerpo y sabor inconfundible de fiesta.', 29.0, '750 ml'),
('Aguardiente Real 1493 8 Años', 'Aguardiente', 95000, 12, 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500&auto=format&fit=crop', 'Edicion especial añejada en barricas de roble, una joya para ocasiones especiales.', 35.0, '750 ml'),

-- Rones
('Ron Medellín Añejo 3 Años', 'Ron', 52000, 40, 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500&auto=format&fit=crop', 'Dorado, aromatico y balanceado. El companero ideal para mezclar con Coca-Cola y limon.', 35.0, '750 ml'),
('Ron Medellín Extra Añejo 8 Años', 'Ron', 78000, 20, 'https://images.unsplash.com/photo-1608885823108-25b4458d9297?w=500&auto=format&fit=crop', 'Madurado pacientemente en barricas de roble americano, sabor suave a caramelo y vainilla.', 35.0, '750 ml'),
('Ron Zacapa Centenario 23 Solera', 'Ron', 280000, 8, 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500&auto=format&fit=crop', 'De las tierras altas de Guatemala, uno de los rones mas premiados del mundo.', 40.0, '750 ml'),

-- Whiskies
('Whisky Buchanan''s DeLuxe 12 Años', 'Whisky', 145000, 25, 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500&auto=format&fit=crop', 'Blended Scotch Whisky suave, con notas citricas y toques sutiles de turba y madera.', 40.0, '750 ml'),
('Whisky Old Parr 12 Años', 'Whisky', 155000, 22, 'https://images.unsplash.com/photo-1569529465841-dfecdab7503b?w=500&auto=format&fit=crop', 'La legendaria botella craquelada. Rico, afrutado y con un final aterciopelado.', 40.0, '750 ml'),
('Whisky Johnnie Walker Black Label', 'Whisky', 160000, 18, 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=500&auto=format&fit=crop', 'Un icono de la destileria escocesa. Notas afrutadas, vainilla cremosa y humo distintivo.', 40.0, '750 ml'),

-- Cervezas
('Six Pack Cerveza Club Colombia Dorada', 'Cervezas', 28000, 60, 'https://images.unsplash.com/photo-1608270546114-1f6305a2e584?w=500&auto=format&fit=crop', 'Cerveza tipo lager dorada brillante, con notas sutiles de lupulo y cebada malteada.', 4.7, 'Six Pack 330ml'),
('Six Pack Cerveza Corona Extra', 'Cervezas', 36000, 50, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&auto=format&fit=crop', 'Cerveza clara mexicana para tomar bien helada con una rodaja de limon.', 4.5, 'Six Pack 355ml'),
('Six Pack Cerveza Águila Light', 'Cervezas', 24000, 70, 'https://images.unsplash.com/photo-1584225064785-c62a8b43d148?w=500&auto=format&fit=crop', 'Suave, refrescante y con bajo contenido calorico para parrandear toda la noche.', 3.4, 'Six Pack 330ml'),

-- Tequilas
('Tequila Don Julio Blanco', 'Tequila', 260000, 10, 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?w=500&auto=format&fit=crop', '100% Agave Azul de Jalisco, con sabor limpio a citricos y notas frescas de pimienta.', 38.0, '750 ml'),
('Tequila José Cuervo Especial Reposado', 'Tequila', 110000, 15, 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=500&auto=format&fit=crop', 'El clasico reposado en barricas de roble, perfecto para preparar margaritas o shots.', 38.0, '750 ml');

-- ==============================================================
-- POLÍTICAS DE ACCESO (Row Level Security - RLS)
-- ==============================================================
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE detalle_pedidos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica productos" ON productos FOR SELECT USING (true);
CREATE POLICY "Lectura publica categorias" ON categorias FOR SELECT USING (true);
CREATE POLICY "Permitir todo a pedidos autenticados o publicos" ON pedidos FOR ALL USING (true);
CREATE POLICY "Permitir todo a detalle pedidos" ON detalle_pedidos FOR ALL USING (true);
CREATE POLICY "Permitir lectura usuarios" ON usuarios FOR SELECT USING (true);
