import logging
from datetime import date, timedelta

from exceptions.errores import InventarioError
from models.perfil import NOMBRE_PERFIL_ADMIN
from repositories.database import get_connection
from services.usuario_service import UsuarioService
from services.categoria_service import CategoriaService
from services.inventario_service import InventarioService
from services.proveedor_service import ProveedorService

logger = logging.getLogger("inventario")

MODULOS = [
    ("Dashboard", "bi-speedometer2", "dashboard", 1),
    ("Productos", "bi-boxes", "productos", 2),
    ("Inventario", "bi-arrow-left-right", "inventario", 3),
    ("Proveedores", "bi-truck", "proveedores", 4),
    ("Reportes", "bi-graph-up", "reportes", 5),
    ("Categorías", "bi-tags", "categorias", 6),
    ("Perfiles", "bi-shield-lock", "perfiles", 7),
    ("Usuarios", "bi-people", "usuarios", 8),
]

USUARIO_ADMIN = {
    "usuario": "admin",
    "clave": "admin123",
    "nombre": "Administrador",
    "correo": "admin@inventario.local",
}

PROVEEDORES = [
    {
        "nombre_proveedor": "Distribuidora Tecnológica SAC",
        "ruc": "20123456786",
        "representante": "Juan Pérez",
        "telefono": "987654321",
        "correo": "ventas@distectec.pe",
        "direccion": "Av. Industrial 123, Lima",
    },
    {
        "nombre_proveedor": "Importaciones del Sur EIRL",
        "ruc": "20456789014",
        "representante": "María López",
        "telefono": "912345678",
        "correo": "contacto@impsur.pe",
        "direccion": "Jr. Comercio 456, Arequipa",
    },
]

CATEGORIAS = [
    {"nombre": "Tecnología", "descripcion": "Equipos y accesorios electrónicos"},
    {"nombre": "Papelería", "descripcion": "Útiles de oficina y escritura"},
    {"nombre": "Alimentos", "descripcion": "Productos de consumo"},
    {"nombre": "Limpieza", "descripcion": "Artículos de aseo y limpieza"},
]

PRODUCTOS = [
    ("Laptop 14''", "Tecnología", 12, 2500.0, 5, None),
    ("Mouse inalámbrico", "Tecnología", 3, 60.0, 10, None),
    ("Teclado mecánico", "Tecnología", 15, 180.0, 5, None),
    ("Monitor 24''", "Tecnología", 7, 650.0, 4, None),
    ("Cuaderno A4", "Papelería", 120, 4.5, 30, None),
    ("Lapicero azul", "Papelería", 8, 1.2, 20, None),
    ("Resma de papel", "Papelería", 40, 22.0, 15, None),
    ("Leche entera 1L", "Alimentos", 40, 5.0, 15, 20),
    ("Café molido 500g", "Alimentos", 25, 22.0, 10, 120),
    ("Arroz 5kg", "Alimentos", 60, 28.0, 20, None),
    ("Detergente 1kg", "Limpieza", 30, 15.0, 12, None),
    ("Jabón líquido", "Limpieza", 4, 9.5, 10, None),
]


def _datos_producto(nombre, categoria, cantidad, precio, stock_minimo, dias_para_vencer):
    """Arma el producto de ejemplo; la fecha de vencimiento es relativa a hoy."""
    fecha = None
    if dias_para_vencer is not None:
        fecha = (date.today() + timedelta(days=dias_para_vencer)).isoformat()
    return {
        "nombre": nombre, "categoria": categoria, "cantidad": cantidad, "precio": precio,
        "stock_minimo": stock_minimo, "fecha_vencimiento": fecha,
    }


def _tabla_vacia(tabla):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        return cursor.fetchone()[0] == 0
    finally:
        cursor.close()
        conn.close()


def _sembrar_perfil_usuario_y_menu():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO perfiles (nombre, descripcion) VALUES (%s, %s)",
            (NOMBRE_PERFIL_ADMIN, "Acceso total al sistema"),
        )
        id_perfil = cursor.lastrowid

        for nombre, icono, ruta, orden in MODULOS:
            cursor.execute(
                "INSERT INTO modulos (nombre, icono, ruta, orden) VALUES (%s, %s, %s, %s)",
                (nombre, icono, ruta, orden),
            )
            cursor.execute(
                "INSERT INTO perfil_modulo (id_perfil, id_modulo) VALUES (%s, %s)",
                (id_perfil, cursor.lastrowid),
            )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    datos_admin = dict(USUARIO_ADMIN, id_perfil=id_perfil, confirmar_admin=True)
    UsuarioService().crear_usuario(datos_admin)


def sembrar_datos_si_vacio():
    """Carga el administrador, el menú y datos de ejemplo si las tablas están vacías."""
    if _tabla_vacia("usuarios"):
        _sembrar_perfil_usuario_y_menu()
        print(f"Menú y usuario 'admin' creados (clave: {USUARIO_ADMIN['clave']}).")

    if _tabla_vacia("proveedores"):
        proveedor_service = ProveedorService()
        for datos in PROVEEDORES:
            proveedor_service.crear_proveedor(datos)
        print(f"{len(PROVEEDORES)} proveedores de ejemplo cargados.")

    if _tabla_vacia("categorias"):
        categoria_service = CategoriaService()
        producto_service = InventarioService()
        mapa_categorias = {}
        for categoria in CATEGORIAS:
            creada = categoria_service.crear_categoria(categoria)
            mapa_categorias[creada.nombre] = creada.id
        for fila in PRODUCTOS:
            datos = _datos_producto(*fila)
            datos["categoria_id"] = mapa_categorias[datos.pop("categoria")]
            try:
                producto_service.crear_producto(datos)
            except InventarioError:
                logger.warning("No se pudo sembrar el producto %s", datos["nombre"], exc_info=True)
        print(
            f"{len(CATEGORIAS)} categorías y {len(PRODUCTOS)} productos de ejemplo cargados."
        )
