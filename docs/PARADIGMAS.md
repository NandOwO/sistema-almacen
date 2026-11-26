# Paradigmas, patrones y decisiones de diseño

Este documento explica cómo el Sistema de Inventario aplica la programación orientada a objetos, los patrones de diseño, el procesamiento vectorizado y el manejo de errores, con referencias al código donde se puede verificar cada punto.

## 1. Arquitectura en capas

Cada petición atraviesa las capas en un solo sentido; ninguna capa conoce a la que está por encima.

```
Navegador (SPA)  →  routes/  →  controllers/  →  services/  →  repositories/  →  MySQL
                     URLs y       HTTP ⇄ JSON     reglas de      consultas SQL
                     permisos                     negocio
                                        models/ (entidades)   patterns/ (patrones)
```

| Paquete | Responsabilidad |
|---|---|
| `routes/` | Define las URLs (blueprints de Flask) y exige sesión y permisos con los decoradores de `sesion.py`. |
| `controllers/` | Lee la petición, llama al servicio y arma la respuesta JSON o el archivo de descarga. |
| `services/` | Reglas de negocio, reportes con NumPy y pandas, importación y exportación. |
| `repositories/` | Única capa que escribe SQL; convierte filas en objetos del dominio. |
| `models/` | Entidades con sus validaciones. |
| `patterns/` | Implementación de los patrones de diseño. |
| `exceptions/` | Errores del dominio con su código HTTP. |

Separar las capas permite probar las reglas de negocio sin base de datos: las pruebas reemplazan los repositorios por versiones en memoria (`tests/conftest.py`).

## 2. Programación orientada a objetos

### Abstracción

`ModeloBase` (`models/base.py`) es una clase abstracta (`ABC`) que fija el contrato de todas las entidades: `to_dict()` es abstracto y `validar()` tiene una implementación por defecto. Los siete modelos heredan de ella, y no se puede instanciar directamente.

### Encapsulamiento

Los datos sensibles se guardan en atributos privados y solo se modifican mediante propiedades que validan el valor:

- **`Producto`** (`models/producto.py`): `_nombre`, `_categoria_id`, `_cantidad`, `_precio`, `_stock_minimo` y `_estado` tienen un `@property` y un *setter*. Un valor inválido (cantidad negativa, precio no numérico, estado fuera de 0–2) lanza `DatosInvalidosError` y el objeto conserva su valor anterior, por lo que nunca queda en un estado inconsistente.
- **`Movimiento`** (`models/movimiento.py`): `stock_anterior`, `stock_nuevo`, `subtotal`, `cantidad` y `tipo_movimiento` son de **solo lectura**. El stock únicamente cambia mediante `aplicar_a_stock()`, que además impide un stock negativo, o mediante `cargar_historial()` al reconstruir un registro guardado. Así el kardex no puede alterarse desde fuera de la clase.
- **`ConexionBD`** (`repositories/database.py`) oculta el pool de conexiones en `_pool`; el resto del sistema solo usa `obtener_conexion()`.

### Herencia

| Clase base | Subclases | Propósito |
|---|---|---|
| `ModeloBase` | `Producto`, `Movimiento`, `Categoria`, `Proveedor`, `Perfil`, `Usuario`, `Modulo` | Contrato común de serialización y validación. |
| `Producto` | `ProductoPerecedero` | Agrega la fecha de vencimiento sin duplicar la lógica de stock y precio. |
| `InventarioError` | 10 errores del dominio | Cada error define su `codigo_http`; un único manejador en `app.py` responde a todos. |
| `FabricaProducto` | `FabricaProductoGeneral`, `FabricaProductoPerecedero` | Factory Method (sección 3). |
| `EstrategiaExportacion` | `ExportacionExcel`, `ExportacionPDF`, `ExportacionCSV`, `ExportacionJSON` | Strategy (sección 3). |

### Polimorfismo

- `ProductoPerecedero` redefine `tipo` y `to_dict()`. Los reportes y el frontend tratan a todos los productos por igual y cada uno responde según su clase.
- `ExportacionService` llama a `estrategia.exportar(titulo, tablas)` sin saber qué formato genera.
- `app.py` responde cualquier `InventarioError` con `error.codigo_http`, sea un 400, un 404 o un 409.

## 3. Patrones de diseño

### Factory Method — creación de productos

**Archivo:** `patterns/fabrica_producto.py`

**Problema:** según los datos recibidos (formulario, base de datos o archivo importado) se debe crear un `Producto` o un `ProductoPerecedero`, y además normalizar los valores por defecto. Repetir esa decisión en cada lugar que crea productos acopla el código a las clases concretas.

| Rol del patrón | Clase |
|---|---|
| Creador abstracto | `FabricaProducto`: `construir()` prepara los atributos comunes y delega en el método fábrica `crear()`. |
| Creadores concretos | `FabricaProductoGeneral` y `FabricaProductoPerecedero` implementan `crear()`. |
| Productos | `Producto` y `ProductoPerecedero`. |
| Selección | `obtener_fabrica(datos)` elige la fábrica según si hay una fecha de vencimiento válida. |

Lo usan `InventarioService` y `ProductoRepository`. Para agregar un tipo nuevo (por ejemplo, productos con número de serie) basta con crear otra fábrica, sin tocar los servicios.

### Strategy — formatos de exportación

**Archivos:** `patterns/estrategias_exportacion.py` (estrategias) y `services/exportacion_service.py` (contexto)

**Problema:** cada reporte se exporta en varios formatos. Un `if formato == ...` en el controlador crece con cada formato nuevo y mezcla la lógica de todos.

| Rol del patrón | Clase |
|---|---|
| Estrategia abstracta | `EstrategiaExportacion`: define `exportar(titulo, tablas)`, `extension` y `tipo_mime`. |
| Estrategias concretas | `ExportacionExcel`, `ExportacionPDF`, `ExportacionCSV`, `ExportacionJSON`. |
| Contexto | `ExportacionService`: registra las estrategias, elige la del formato pedido y arma el archivo con nombre y tipo MIME. |

CSV y JSON se agregaron después que Excel y PDF creando dos clases y registrándolas, sin modificar el controlador ni las estrategias existentes (principio abierto/cerrado). La prueba `test_estrategias_intercambiables` inyecta una estrategia nueva para demostrarlo.

### Singleton — pool de conexiones

**Archivos:** `patterns/singleton.py` (metaclase) y `repositories/database.py` (`ConexionBD`)

**Problema:** crear un pool de conexiones por consulta repetiría la autenticación con MySQL en cada petición; tener varios pools desperdiciaría conexiones.

- `Singleton` es una **metaclase** que guarda una instancia por clase y usa un `threading.Lock` con doble verificación, porque Flask atiende peticiones en varios hilos.
- `ConexionBD(metaclass=Singleton)` crea el pool la primera vez que se pide una conexión y lo recrea si quedó inservible.
- `reiniciar()` descarta la instancia; se usa en las pruebas para aislar cada caso.

## 4. Paradigma funcional

Los indicadores simples del dashboard (`services/reportes_service.py`) están escritos como funciones puras con `reduce`, `filter` y `lambda`: `valor_total_inventario`, `unidades_totales`, `valor_por_categoria`, `conteo_por_categoria`, `productos_bajo_stock` y `resumen_movimientos`. No modifican sus argumentos y su resultado depende solo de la entrada.

## 5. Procesamiento vectorizado con NumPy y pandas

Los reportes que procesan muchas filas operan sobre columnas completas en lugar de recorrer fila por fila:

| Reporte | Técnica |
|---|---|
| Predicción de reposición | `groupby().sum()` del consumo; `np.where` para días restantes y cantidad sugerida; `np.select` para clasificar la urgencia; `sort_values(kind="stable", na_position="last")`. |
| Vencimientos | `pd.to_datetime(errors="coerce")`, resta de fechas con `.dt.days` y `np.select` para el estado. |
| Movimientos por mes | `pd.period_range` para los meses y `pivot_table` para sumar entradas y salidas. |
| Bajo stock | Máscaras booleanas de NumPy y `np.maximum` para el faltante. |
| Inventario valorizado | `groupby().agg()` con varias métricas y `nlargest`. |
| Compras por proveedor | `groupby().agg()`. |
| Exportación | El PDF formatea todas las celdas con `DataFrame.map`; el Excel calcula anchos con `.str.len().max()`. |
| Importación | Limpieza con `pd.to_numeric(errors="coerce")`, normalización de texto con `.str`, detección de duplicados con `duplicated()` y validación de todas las filas a la vez con `np.select`. |

La prueba `test_coincide_con_el_calculo_fila_por_fila` compara la predicción vectorizada con un cálculo tradicional fila por fila sobre 60 productos y 150 movimientos aleatorios.

### Archivos estructurados

- **Lectura:** `ImportacionService` lee CSV (`pd.read_csv`) y JSON (`pd.read_json`) para importar productos.
- **Escritura:** las estrategias de exportación generan Excel, PDF, CSV (`DataFrame.to_csv`) y JSON (`DataFrame.to_json`).
- **Datos de prueba:** `data/productos_ejemplo.csv`, `data/productos_ejemplo.json` y `data/productos_con_errores.csv`.

## 6. Manejo de excepciones

- **Errores del dominio:** las reglas de negocio lanzan subclases de `InventarioError`; `app.py` las convierte en respuestas JSON con su código. Los errores HTTP (404, 405, 413) también se responden en JSON, y cualquier otro error se registra en el log y responde 500 sin exponer detalles internos.
- **try-except-finally al leer archivos:** `ImportacionService.leer_archivo` traduce `UnicodeDecodeError`, `ParserError`, `EmptyDataError` y `ValueError` en mensajes claros, y en el bloque `finally` cierra el archivo siempre, también cuando la lectura falla.
- **Errores por fila:** en la importación, un producto inválido no detiene el resto; se registra el número de fila y el motivo.
- **Recursos de base de datos:** cada método de los repositorios cierra cursor y conexión en un `finally`. El registro de un movimiento hace `rollback` si falla, para que el stock y el kardex nunca queden desalineados.
- **Datos de ejemplo:** la siembra inicial registra en el log el producto que no se pudo crear y continúa con los demás.

## 7. Otros paradigmas

- **Declarativo:** las consultas SQL de `repositories/` y las agregaciones de pandas describen qué resultado se quiere, no cómo recorrer los datos.
- **Orientado a eventos:** el frontend (`frontend/js/`) reacciona a los eventos del usuario y del navegador sin recargar la página.

## 8. Relación con la rúbrica

| Criterio | Dónde se cumple |
|---|---|
| POO: encapsulamiento, herencia y polimorfismo | Sección 2; `models/`, `exceptions/`, `patterns/` |
| Dos o más patrones de diseño | Sección 3; `patterns/` |
| NumPy y pandas vectorizados | Sección 5; `services/reportes_service.py`, `services/importacion_service.py` |
| Lectura y escritura de CSV y JSON | Sección 5; `services/importacion_service.py`, `patterns/estrategias_exportacion.py`, `data/` |
| Interfaz con controles adecuados y sin bloqueos | `frontend/`: selectores de fecha, listas desplegables, tablas, gráficos (Chart.js), indicadores de carga en importación y exportación |
| Paquetes y módulos reutilizables | Sección 1; cada paquete tiene su `__init__.py` |
| PEP 8 | Verificado con `flake8` (configuración en `.flake8`) |
| try-except-finally | Sección 6 |
| Docstrings | Clases, métodos y funciones públicas de `backend/` |
| Pruebas unitarias | `tests/`: 165 pruebas con pytest |
