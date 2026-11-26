from datetime import date
from functools import reduce

import numpy as np
import pandas as pd

DIAS_CRITICO = 7
DIAS_ATENCION = 15


def _registros(df):
    """Convierte un DataFrame en registros JSON nativos, con None en lugar de NaN."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def _df_productos(productos, columnas=None):
    df = pd.DataFrame([p.to_dict() for p in productos])
    if "fecha_vencimiento" not in df:
        df["fecha_vencimiento"] = None
    return df[columnas] if columnas else df


def _df_movimientos(movimientos):
    return pd.DataFrame(
        [{
            "id_producto": m.id_producto,
            "tipo_movimiento": m.tipo_movimiento,
            "cantidad": m.cantidad,
            "subtotal": float(m.subtotal or 0),
            "proveedor": m.proveedor_nombre or "—",
            "fecha": m.fecha,
        } for m in movimientos],
        columns=["id_producto", "tipo_movimiento", "cantidad", "subtotal", "proveedor", "fecha"],
    )


def valor_total_inventario(productos):
    """Suma el valor de todos los productos (reduce)."""
    return round(reduce(lambda acc, p: acc + p.valor_total, productos, 0.0), 2)


def unidades_totales(productos):
    """Suma las unidades en stock (reduce)."""
    return reduce(lambda acc, p: acc + p.cantidad, productos, 0)


def productos_bajo_stock(productos):
    """Productos que necesitan reposición (filter)."""
    return list(filter(lambda p: p.necesita_reposicion, productos))


def valor_por_categoria(productos):
    """Valor del inventario por categoría (reduce sobre un diccionario)."""
    return reduce(
        lambda acc, p: {
            **acc,
            p.categoria: round(acc.get(p.categoria, 0.0) + p.valor_total, 2),
        },
        productos,
        {},
    )


def conteo_por_categoria(productos):
    """Cantidad de productos por categoría (reduce)."""
    return reduce(
        lambda acc, p: {**acc, p.categoria: acc.get(p.categoria, 0) + 1}, productos, {}
    )


def generar_resumen(productos):
    """Indicadores generales del inventario para el dashboard."""
    bajo_stock = productos_bajo_stock(productos)
    venc = reporte_vencimientos(productos)["resumen"]
    return {
        "total_productos": len(productos),
        "unidades_totales": unidades_totales(productos),
        "valor_total": valor_total_inventario(productos),
        "categorias": len(conteo_por_categoria(productos)),
        "productos_bajo_stock": len(bajo_stock),
        "nombres_bajo_stock": [p.nombre for p in bajo_stock],
        "valor_por_categoria": valor_por_categoria(productos),
        "vencidos": venc["vencidos"],
        "por_vencer": venc["por_vencer"],
    }


def analisis_pandas(productos):
    """Agrega el inventario por categoría y obtiene los productos de mayor valor."""
    if not productos:
        return {"por_categoria": [], "top_productos": [], "totales": {}}

    df = _df_productos(productos)

    por_categoria = (
        df.groupby("categoria")
        .agg(
            productos=("nombre", "count"),
            unidades=("cantidad", "sum"),
            valor=("valor_total", "sum"),
            precio_promedio=("precio", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("valor", ascending=False)
    )

    top = df.nlargest(5, "valor_total", keep="first")[["nombre", "categoria", "valor_total"]]

    totales = {
        "valor_total": round(float(df["valor_total"].sum()), 2),
        "unidades": int(df["cantidad"].sum()),
        "productos": int(len(df)),
    }
    return {
        "por_categoria": _registros(por_categoria),
        "top_productos": _registros(top),
        "totales": totales,
    }


def _suma(movimientos, condicion, campo):
    return reduce(
        lambda acc, m: acc + (getattr(m, campo) or 0 if condicion(m) else 0),
        movimientos, 0,
    )


def resumen_movimientos(movimientos):
    """Cuenta entradas, salidas y ajustes y suma unidades y compras."""
    def es(tipo):
        return lambda m: m.tipo_movimiento == tipo

    entradas = list(filter(es("ENTRADA"), movimientos))
    salidas = list(filter(es("SALIDA"), movimientos))
    ajustes = list(filter(es("AJUSTE"), movimientos))
    valor_comprado = round(
        reduce(lambda acc, m: acc + float(m.subtotal or 0), entradas, 0.0), 2
    )
    return {
        "total": len(movimientos),
        "entradas": len(entradas),
        "salidas": len(salidas),
        "ajustes": len(ajustes),
        "unidades_entrada": _suma(movimientos, es("ENTRADA"), "cantidad"),
        "unidades_salida": _suma(movimientos, es("SALIDA"), "cantidad"),
        "valor_comprado": valor_comprado,
    }


def compras_por_proveedor(movimientos):
    """Totaliza las entradas por proveedor con una agregación de pandas."""
    entradas = [m for m in movimientos if m.tipo_movimiento == "ENTRADA"]
    if not entradas:
        return {"por_proveedor": [], "resumen": resumen_movimientos([])}

    por_proveedor = (
        _df_movimientos(entradas)
        .groupby("proveedor")
        .agg(movimientos=("id_producto", "size"),
             unidades=("cantidad", "sum"),
             total=("subtotal", "sum"))
        .round(2)
        .reset_index()
        .sort_values("total", ascending=False)
    )
    return {
        "por_proveedor": _registros(por_proveedor),
        "resumen": resumen_movimientos(entradas),
    }


def detalle_bajo_stock(productos):
    """Productos en o bajo su stock mínimo, con las unidades que faltan."""
    if not productos:
        return []
    df = _df_productos(productos)
    bajo = df[df["cantidad"] <= df["stock_minimo"]].copy()
    bajo["faltante"] = np.maximum(0, bajo["stock_minimo"] - bajo["cantidad"])
    return _registros(bajo)


def resumen_bajo_stock(productos):
    """Totales de productos bajo stock y sin stock, con máscaras de NumPy."""
    if not productos:
        return {"total_productos": 0, "bajo_stock": 0, "sin_stock": 0, "unidades_faltantes": 0}

    cantidad = np.array([p.cantidad for p in productos])
    minimo = np.array([p.stock_minimo for p in productos])
    bajo = cantidad <= minimo
    return {
        "total_productos": len(productos),
        "bajo_stock": int(bajo.sum()),
        "sin_stock": int((bajo & (cantidad == 0)).sum()),
        "unidades_faltantes": int(np.maximum(0, minimo - cantidad)[bajo].sum()),
    }


def prediccion_reposicion(productos, salidas, ventana_dias=30, cobertura_dias=30):
    """Estima consumo diario, días hasta agotarse y cantidad sugerida de compra."""
    ventana_dias = max(1, int(ventana_dias))
    resumen_vacio = {
        "productos": 0, "por_agotarse": 0, "en_atencion": 0,
        "sin_consumo": 0, "unidades_comprar": 0,
    }
    if not productos:
        return {"productos": [], "resumen": resumen_vacio}

    df = _df_productos(productos, ["id", "nombre", "categoria", "cantidad", "stock_minimo"])
    consumo = _df_movimientos(salidas).groupby("id_producto")["cantidad"].sum()

    vendidas = df["id"].map(consumo).fillna(0).to_numpy(dtype=float)
    cantidad = df["cantidad"].to_numpy(dtype=float)
    minimo = df["stock_minimo"].to_numpy(dtype=float)

    diario = np.round(vendidas / ventana_dias, 2)
    con_consumo = diario > 0
    dias = np.where(con_consumo, np.floor(cantidad / np.where(con_consumo, diario, 1)), np.nan)
    sugerido = np.where(
        con_consumo,
        np.maximum(0, np.ceil(diario * cobertura_dias - cantidad)),
        np.maximum(0, minimo - cantidad),
    )
    urgencia = np.select(
        [cantidad == 0, ~con_consumo, dias <= DIAS_CRITICO, dias <= DIAS_ATENCION],
        ["SIN STOCK", "SIN CONSUMO", "CRÍTICO", "ATENCIÓN"],
        default="OK",
    )

    df["consumo_diario"] = diario
    df["dias_restantes"] = pd.array(dias, dtype="Int64")
    df["sugerido"] = sugerido.astype(int)
    df["urgencia"] = urgencia
    df = df.sort_values("dias_restantes", na_position="last", kind="stable")

    con_dias = ~np.isnan(dias)
    return {
        "productos": _registros(df),
        "resumen": {
            "productos": len(df),
            "por_agotarse": int((con_dias & (dias <= DIAS_CRITICO)).sum()),
            "en_atencion": int((con_dias & (dias > DIAS_CRITICO) & (dias <= DIAS_ATENCION)).sum()),
            "sin_consumo": int((~con_consumo).sum()),
            "unidades_comprar": int(sugerido.sum()),
        },
    }


def movimientos_por_mes(movimientos, meses=6):
    """Unidades de entrada y salida de los últimos meses, agrupadas por mes."""
    periodos = pd.period_range(end=pd.Period(date.today(), freq="M"), periods=meses, freq="M")
    etiquetas = list(periodos.strftime("%Y-%m"))

    df = _df_movimientos(movimientos)
    df["mes"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%Y-%m")
    tabla = (
        df[df["tipo_movimiento"].isin(["ENTRADA", "SALIDA"])]
        .pivot_table(index="mes", columns="tipo_movimiento", values="cantidad",
                     aggfunc="sum", fill_value=0)
        .reindex(index=etiquetas, columns=["ENTRADA", "SALIDA"], fill_value=0)
        .fillna(0)
        .astype(int)
    )
    return {
        "meses": etiquetas,
        "entradas": tabla["ENTRADA"].tolist(),
        "salidas": tabla["SALIDA"].tolist(),
    }


def reporte_vencimientos(productos, dias_alerta=30):
    """Clasifica los perecederos en vencidos, por vencer y vigentes."""
    columnas = ["id", "nombre", "categoria", "cantidad", "fecha_vencimiento"]
    df = _df_productos(productos, columnas) if productos else pd.DataFrame(columns=columnas)

    fechas = pd.to_datetime(df["fecha_vencimiento"], format="%Y-%m-%d", errors="coerce")
    df = df[fechas.notna()].copy()
    df["dias_restantes"] = (fechas[fechas.notna()] - pd.Timestamp(date.today())).dt.days.astype(int)
    df["estado_venc"] = np.select(
        [df["dias_restantes"] < 0, df["dias_restantes"] <= dias_alerta],
        ["VENCIDO", "POR VENCER"],
        default="VIGENTE",
    )
    df = df.sort_values("dias_restantes", kind="stable")

    conteo = df["estado_venc"].value_counts()
    en_riesgo = df["estado_venc"] != "VIGENTE"
    return {
        "productos": _registros(df),
        "resumen": {
            "perecederos": len(df),
            "vencidos": int(conteo.get("VENCIDO", 0)),
            "por_vencer": int(conteo.get("POR VENCER", 0)),
            "vigentes": int(conteo.get("VIGENTE", 0)),
            "unidades_riesgo": int(df.loc[en_riesgo, "cantidad"].sum()),
        },
    }
