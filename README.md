# Sistema de Inventario

Aplicación web de gestión de inventario desarrollada como proyecto de **Programación Multiparadigma**. Permite administrar productos, categorías, proveedores, usuarios y perfiles con permisos; registrar entradas, salidas y ajustes de stock con kardex; generar reportes con gráficos, predicción de reposición y exportación a Excel, PDF, CSV y JSON; e importar productos de forma masiva desde archivos CSV o JSON.

## Características

- **Autenticación** con sesión, contraseñas hasheadas y permisos por perfil (cada perfil ve solo sus módulos).
- **Catálogo**: productos (incluye perecederos con fecha de vencimiento), categorías y proveedores.
- **Inventario**: entradas, salidas y ajustes por producto, con historial (kardex), stock transaccional y documento obligatorio en compras y ventas.
- **Reportes** (6): valorizado, movimientos/kardex, reposición sugerida, vencimientos, bajo stock y compras por proveedor, con filtros, gráficos y exportación a **Excel**, **PDF**, **CSV** y **JSON**. Los cálculos usan operaciones vectorizadas de NumPy y pandas.
- **Importación masiva** de productos desde CSV o JSON: limpia y valida todas las filas, importa las válidas e informa el motivo de cada fila rechazada.
- **Innovación**: *predicción de reposición* (consumo diario, días hasta agotarse y cantidad sugerida de compra a partir del historial) y *alertas de vencimiento*.
- **Eliminación lógica** en 3 estados (activo / inactivo / eliminado) sin perder historial.
- **SPA sin recargas**: toda la navegación y las acciones ocurren sin recargar la página ni cambiar la URL.
- **Diseño responsivo**: en móvil las tablas colapsan con botón «+» (patrón DataTables) y las tarjetas se apilan.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Flask, MySQL (mysql-connector), NumPy, pandas, openpyxl, fpdf2 |
| Frontend | JavaScript (módulos ES), Bootstrap 5, Chart.js, SweetAlert2 |
| Base de datos | MySQL / MariaDB |
| Pruebas y calidad | pytest, flake8 (PEP 8) |

## Requisitos

- Python 3.10 o superior
- MySQL o MariaDB en ejecución (XAMPP, WAMP o instalación directa)

## Instalación

1. **Clonar/copiar el proyecto** y abrir una terminal en su raíz.

2. **Crear la base de datos**: ejecutar `schema.sql` en MySQL (phpMyAdmin → pestaña SQL, o consola):

   ```sql
   SOURCE schema.sql;
   ```

3. **Configurar credenciales** (opcional): si tu MySQL tiene contraseña u otros datos de conexión, crear un archivo `.env` en la raíz del proyecto con estas variables (sin `.env`, se usa `root` sin contraseña en `localhost`):

   ```env
   SECRET_KEY=una-clave-larga-y-aleatoria
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=tu-contraseña
   DB_NAME=inventario
   DB_PORT=3306
   PUERTO=5000
   ```

4. **Crear el entorno virtual e instalar dependencias**:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Ejecutar las pruebas** (desde la raíz del proyecto; no necesitan MySQL):

   ```powershell
   pytest
   ```

6. **Arrancar el servidor**:

   ```powershell
   cd backend
   python app.py
   ```

7. Abrir **http://localhost:5000** e iniciar sesión:

   | Usuario | Clave |
   |---|---|
   | `admin` | `admin123` |

   La primera vez, el sistema siembra automáticamente el perfil Administrador, los módulos del menú, proveedores, categorías y productos de ejemplo.

## Importar productos

En **Productos → Importar** se puede subir un archivo `.csv` o `.json` (máximo 2 MB y 1000 filas) con estas columnas:

| Columna | Obligatoria | Formato |
|---|---|---|
| `nombre` | Sí | Texto |
| `categoria` | Sí | Nombre de una categoría existente |
| `cantidad` | Sí | Entero no negativo |
| `precio` | Sí | Número no negativo |
| `stock_minimo` | No | Entero no negativo (por defecto 5) |
| `fecha_vencimiento` | No | `AAAA-MM-DD`, no anterior a hoy |

La carpeta `data/` incluye `productos_ejemplo.csv`, `productos_ejemplo.json` y `productos_con_errores.csv` (este último con errores a propósito para ver la validación).

## Pruebas y calidad

```powershell
pytest            # 152 pruebas: modelos, patrones, servicios, reportes, importación, validadores y API
pytest -v         # con el nombre de cada prueba
pip install flake8
flake8            # revisión PEP 8 con la configuración de .flake8
```

Las pruebas reemplazan los repositorios por versiones en memoria, así que se ejecutan sin base de datos.

## Estructura del proyecto

```
SistemaInventario/
├── schema.sql               # Estructura de la base de datos
├── requirements.txt
├── pyproject.toml           # Configuración de pytest
├── .flake8                  # Configuración de PEP 8
├── docs/PARADIGMAS.md       # POO, patrones, vectorización y excepciones
├── data/                    # Archivos CSV/JSON de ejemplo
├── tests/                   # Pruebas unitarias (pytest)
├── backend/
│   ├── app.py               # Punto de entrada (Flask)
│   ├── config.py            # Configuración (lee .env)
│   ├── sesion.py            # Sesión y permisos por módulo
│   ├── validadores.py       # Validaciones reutilizables
│   ├── seed_data.py         # Datos iniciales
│   ├── models/              # POO: entidades y reglas propias
│   ├── patterns/            # Factory Method, Strategy y Singleton
│   ├── repositories/        # Acceso a MySQL (SQL)
│   ├── services/            # Reglas de negocio, reportes, importación y exportación
│   ├── controllers/         # Petición HTTP → service → JSON
│   ├── routes/              # URLs (blueprints) + permisos
│   └── exceptions/          # Errores del dominio con código HTTP
└── frontend/
    ├── index.html           # Shell de la SPA (login + layout)
    ├── css/estilos.css
    ├── js/
    │   ├── main.js          # Arranque y sesión
    │   ├── router.js        # Navegación sin recargas + tablas responsivas
    │   ├── api/             # Única capa que habla con el backend
    │   ├── utils/           # Helpers y validaciones
    │   └── views/           # Lógica de cada módulo y reporte
    └── views/               # Fragmentos HTML de cada módulo
```

## Diagrama entidad-relación

```mermaid
erDiagram
    PERFILES ||--o{ USUARIOS : "tiene"
    PERFILES ||--o{ PERFIL_MODULO : "permite"
    MODULOS  ||--o{ PERFIL_MODULO : "se asigna"
    CATEGORIAS ||--o{ PRODUCTOS : "agrupa"
    PRODUCTOS  ||--o{ MOVIMIENTOS : "registra"
    PROVEEDORES ||--o{ MOVIMIENTOS : "abastece"
    USUARIOS    ||--o{ MOVIMIENTOS : "ejecuta"

    PERFILES {
        int id_perfil PK
        varchar nombre
        tinyint estado
    }
    USUARIOS {
        int id_usuario PK
        varchar usuario
        varchar clave "hash"
        int id_perfil FK
        tinyint estado
    }
    MODULOS {
        int id_modulo PK
        varchar nombre
        varchar icono
        varchar ruta
        int orden
    }
    PERFIL_MODULO {
        int id_perfil PK, FK
        int id_modulo PK, FK
    }
    CATEGORIAS {
        int id PK
        varchar nombre
        tinyint estado
    }
    PRODUCTOS {
        int id PK
        varchar nombre
        int categoria_id FK
        int cantidad
        decimal precio
        int stock_minimo
        date fecha_vencimiento
        tinyint estado
    }
    PROVEEDORES {
        int id_proveedor PK
        varchar nombre_proveedor
        varchar ruc
        tinyint estado
    }
    MOVIMIENTOS {
        int id PK
        int id_producto FK
        int id_proveedor FK
        int id_usuario FK
        varchar tipo_movimiento "ENTRADA|SALIDA|AJUSTE"
        varchar motivo
        int cantidad
        int stock_anterior
        int stock_nuevo
        varchar numero_documento
        decimal precio_compra
        decimal subtotal
        datetime fecha
    }
```

> Los estados son: `1` activo, `0` inactivo, `2` eliminado (eliminación lógica).

## Paradigmas y patrones

| Aspecto | Aplicación |
|---|---|
| **Orientado a objetos** | Clase abstracta `ModeloBase`; encapsulamiento con propiedades validadas en `Producto` y `Movimiento`; herencia `ProductoPerecedero → Producto` y jerarquía de excepciones; polimorfismo en `tipo`, `to_dict()` y `exportar()`. |
| **Patrones de diseño** | **Factory Method** para crear productos, **Strategy** para los formatos de exportación y **Singleton** para el pool de conexiones (`backend/patterns/`). |
| **Funcional** | Indicadores con `reduce`, `filter` y `lambda` en `services/reportes_service.py`. |
| **Vectorizado** | Reportes e importación con operaciones de NumPy y pandas sobre columnas completas. |
| **Declarativo** | Consultas SQL y agregaciones de pandas. |
| **Orientado a eventos** | Frontend que reacciona a las acciones del usuario sin recargar la página. |

El detalle, con la justificación de cada decisión y su ubicación en el código, está en [docs/PARADIGMAS.md](docs/PARADIGMAS.md).
