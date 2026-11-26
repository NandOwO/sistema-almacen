import logging
from pathlib import Path

import numpy as np
import pandas as pd

from exceptions.errores import DatosInvalidosError, InventarioError
from repositories.categoria_repository import CategoriaRepository
from services.inventario_service import InventarioService

COLUMNAS_REQUERIDAS = ("nombre", "categoria", "cantidad", "precio")
COLUMNAS_OPCIONALES = ("stock_minimo", "fecha_vencimiento")
STOCK_MINIMO_POR_DEFECTO = 5
LIMITE_FILAS = 1000
PRIMERA_FILA = {".csv": 2, ".json": 1}

logger = logging.getLogger("inventario")


def _a_registros(df):
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def _numero(serie):
    return pd.to_numeric(serie, errors="coerce")


def _vacio(serie):
    return serie.isna() | (serie.astype("string").str.strip() == "")


class ImportacionService:
    """Carga masiva de productos desde archivos CSV o JSON."""

    def __init__(self, inventario=None, categoria_repo=None):
        self.inventario = inventario or InventarioService()
        self.categoria_repo = categoria_repo or CategoriaRepository()

    def leer_archivo(self, archivo, nombre_archivo):
        """Lee el archivo en un DataFrame y lo cierra siempre, aunque falle la lectura."""
        extension = Path(nombre_archivo or "").suffix.lower()
        lectores = {".csv": self._leer_csv, ".json": self._leer_json}
        if extension not in lectores:
            archivo.close()
            raise DatosInvalidosError("Formato no soportado: use un archivo .csv o .json.")
        try:
            df = lectores[extension](archivo)
        except UnicodeDecodeError:
            raise DatosInvalidosError("El archivo debe estar codificado en UTF-8.")
        except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError):
            raise DatosInvalidosError("El archivo está vacío o no tiene un formato válido.")
        finally:
            archivo.close()

        if df.empty:
            raise DatosInvalidosError("El archivo no contiene filas.")
        if len(df) > LIMITE_FILAS:
            raise DatosInvalidosError(f"El archivo supera el máximo de {LIMITE_FILAS} filas.")
        return df

    @staticmethod
    def _leer_csv(archivo):
        return pd.read_csv(archivo, encoding="utf-8-sig", dtype=str, skipinitialspace=True)

    @staticmethod
    def _leer_json(archivo):
        df = pd.read_json(archivo, orient="records", dtype=False)
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Se esperaba una lista de objetos.")
        return df

    def limpiar(self, df, primera_fila=2):
        """Normaliza columnas y valores; separa filas válidas de las rechazadas."""
        df = df.rename(columns=lambda c: str(c).strip().lower())
        faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
        if faltantes:
            raise DatosInvalidosError(f"Faltan columnas obligatorias: {', '.join(faltantes)}.")
        for columna in COLUMNAS_OPCIONALES:
            if columna not in df.columns:
                df[columna] = None

        datos = pd.DataFrame({"fila": np.arange(primera_fila, primera_fila + len(df))})
        for columna in ("nombre", "categoria", "fecha_vencimiento"):
            texto = df[columna].astype("string").str.split().str.join(" ")
            datos[columna] = texto.where(texto != "", pd.NA).to_numpy()

        cantidad = _numero(df["cantidad"]).to_numpy()
        precio = _numero(df["precio"]).to_numpy()
        stock_vacio = _vacio(df["stock_minimo"]).to_numpy()
        stock = np.where(stock_vacio, STOCK_MINIMO_POR_DEFECTO, _numero(df["stock_minimo"]))

        nombre = datos["nombre"]
        sin_nombre = nombre.isna().to_numpy()
        duplicado = (nombre.str.lower().duplicated(keep="first") & nombre.notna()).to_numpy()

        motivo = np.select(
            [
                sin_nombre,
                datos["categoria"].isna().to_numpy(),
                np.isnan(cantidad) | (cantidad < 0) | (cantidad % 1 != 0),
                np.isnan(precio) | (precio < 0),
                np.isnan(stock) | (stock < 0) | (stock % 1 != 0),
                duplicado,
            ],
            [
                "Falta el nombre del producto.",
                "Falta la categoría.",
                "La cantidad debe ser un entero no negativo.",
                "El precio debe ser un número no negativo.",
                "El stock mínimo debe ser un entero no negativo.",
                "Producto repetido dentro del archivo.",
            ],
            default="",
        )

        datos["cantidad"] = np.nan_to_num(cantidad).astype(int)
        datos["precio"] = np.round(np.nan_to_num(precio), 2)
        datos["stock_minimo"] = np.nan_to_num(stock).astype(int)

        rechazadas = datos.loc[motivo != "", ["fila"]].assign(error=motivo[motivo != ""])
        return datos[motivo == ""].copy(), _a_registros(rechazadas)

    def importar_productos(self, archivo, nombre_archivo):
        """Importa los productos válidos y devuelve el detalle de las filas rechazadas."""
        extension = Path(nombre_archivo or "").suffix.lower()
        df = self.leer_archivo(archivo, nombre_archivo)
        validos, errores = self.limpiar(df, PRIMERA_FILA.get(extension, 1))

        categorias = {c.nombre.lower(): c.id for c in self.categoria_repo.listar(solo_activos=True)}
        existentes = {p.nombre.lower() for p in self.inventario.listar_productos()}

        validos["categoria_id"] = validos["categoria"].str.lower().map(categorias)
        sin_categoria = validos["categoria_id"].isna()
        ya_existe = validos["nombre"].str.lower().isin(existentes)

        errores += [
            {"fila": int(f), "error": f"La categoría '{c}' no existe."}
            for f, c in validos.loc[sin_categoria, ["fila", "categoria"]].itertuples(index=False)
        ]
        errores += [
            {"fila": int(f), "error": "Ya existe un producto con ese nombre."}
            for f in validos.loc[~sin_categoria & ya_existe, "fila"]
        ]

        importados = 0
        for registro in _a_registros(validos[~sin_categoria & ~ya_existe]):
            try:
                self.inventario.crear_producto(registro)
                importados += 1
            except InventarioError as error:
                errores.append({"fila": registro["fila"], "error": str(error)})

        logger.info("Importación de %s: %d importados, %d rechazados",
                    nombre_archivo, importados, len(errores))
        return {
            "importados": importados,
            "rechazados": len(errores),
            "errores": sorted(errores, key=lambda e: e["fila"]),
        }
