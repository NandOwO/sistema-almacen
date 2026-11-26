import json
from datetime import date
from math import ceil

import numpy as np
import pytest

from services import reportes_service as rs
from tests.conftest import movimiento, producto


@pytest.fixture
def salidas():
    return [
        movimiento(2, 20, hace_dias=2),
        movimiento(2, 15, hace_dias=10),
        movimiento(1, 6, hace_dias=5),
        movimiento(5, 60, hace_dias=1),
    ]


class TestResumenGeneral:
    def test_totales_funcionales(self, productos_muestra):
        assert rs.valor_total_inventario(productos_muestra) == 30953.1
        assert rs.unidades_totales(productos_muestra) == 87
        assert rs.valor_por_categoria(productos_muestra) == {
            "Tecnología": 30180.0, "Papelería": 0.0, "Alimentos": 773.1,
        }
        assert rs.conteo_por_categoria(productos_muestra) == {
            "Tecnología": 2, "Papelería": 1, "Alimentos": 3,
        }

    def test_generar_resumen(self, productos_muestra):
        resumen = rs.generar_resumen(productos_muestra)
        assert resumen["productos_bajo_stock"] == 3
        assert resumen["nombres_bajo_stock"] == ["Mouse inalámbrico", "Cuaderno A4", "Yogurt fresa"]
        assert (resumen["vencidos"], resumen["por_vencer"]) == (1, 1)


class TestAnalisisPandas:
    def test_agrupa_por_categoria_ordenado_por_valor(self, productos_muestra):
        datos = rs.analisis_pandas(productos_muestra)
        assert datos["por_categoria"] == [
            {"categoria": "Tecnología", "productos": 2, "unidades": 15, "valor": 30180.0, "precio_promedio": 1280.0},
            {"categoria": "Alimentos", "productos": 3, "unidades": 72, "valor": 773.1, "precio_promedio": 10.1},
            {"categoria": "Papelería", "productos": 1, "unidades": 0, "valor": 0.0, "precio_promedio": 4.5},
        ]
        assert datos["top_productos"][0]["nombre"] == "Laptop 14"
        assert len(datos["top_productos"]) == 5
        assert datos["totales"] == {"valor_total": 30953.1, "unidades": 87, "productos": 6}

    def test_sin_productos(self):
        assert rs.analisis_pandas([]) == {"por_categoria": [], "top_productos": [], "totales": {}}


class TestBajoStock:
    def test_resumen(self, productos_muestra):
        assert rs.resumen_bajo_stock(productos_muestra) == {
            "total_productos": 6, "bajo_stock": 3, "sin_stock": 1, "unidades_faltantes": 37,
        }

    def test_detalle_calcula_faltante(self, productos_muestra):
        detalle = rs.detalle_bajo_stock(productos_muestra)
        assert [(d["nombre"], d["faltante"]) for d in detalle] == [
            ("Mouse inalámbrico", 7), ("Cuaderno A4", 30), ("Yogurt fresa", 0),
        ]

    def test_sin_productos(self):
        assert rs.resumen_bajo_stock([])["bajo_stock"] == 0
        assert rs.detalle_bajo_stock([]) == []


class TestPrediccionReposicion:
    def test_calcula_consumo_dias_y_sugerido(self, productos_muestra, salidas):
        datos = rs.prediccion_reposicion(productos_muestra, salidas, ventana_dias=30, cobertura_dias=30)
        filas = {f["id"]: f for f in datos["productos"]}

        assert (filas[2]["consumo_diario"], filas[2]["dias_restantes"], filas[2]["sugerido"]) == (1.17, 2, 33)
        assert filas[2]["urgencia"] == "CRÍTICO"
        assert (filas[5]["dias_restantes"], filas[5]["sugerido"], filas[5]["urgencia"]) == (12, 35, "ATENCIÓN")
        assert (filas[1]["dias_restantes"], filas[1]["sugerido"], filas[1]["urgencia"]) == (60, 0, "OK")
        assert (filas[3]["dias_restantes"], filas[3]["sugerido"], filas[3]["urgencia"]) == (None, 30, "SIN STOCK")
        assert (filas[4]["urgencia"], filas[4]["sugerido"]) == ("SIN CONSUMO", 0)

    def test_ordena_por_dias_restantes_con_vacios_al_final(self, productos_muestra, salidas):
        datos = rs.prediccion_reposicion(productos_muestra, salidas)
        assert [f["id"] for f in datos["productos"]] == [2, 5, 1, 3, 4, 6]

    def test_resumen(self, productos_muestra, salidas):
        assert rs.prediccion_reposicion(productos_muestra, salidas)["resumen"] == {
            "productos": 6, "por_agotarse": 1, "en_atencion": 1, "sin_consumo": 3, "unidades_comprar": 98,
        }

    def test_resultado_serializable_a_json(self, productos_muestra, salidas):
        texto = json.dumps(rs.prediccion_reposicion(productos_muestra, salidas))
        assert "NaN" not in texto

    def test_ventana_minima_de_un_dia(self, productos_muestra, salidas):
        datos = rs.prediccion_reposicion(productos_muestra, salidas, ventana_dias=0)
        assert next(f for f in datos["productos"] if f["id"] == 2)["consumo_diario"] == 35.0

    def test_sin_productos(self):
        assert rs.prediccion_reposicion([], [])["productos"] == []

    def test_coincide_con_el_calculo_fila_por_fila(self):
        generador = np.random.default_rng(42)
        productos = [
            producto(i, f"Producto {i}", cantidad=int(generador.integers(0, 80)),
                     stock_minimo=int(generador.integers(0, 20)))
            for i in range(1, 61)
        ]
        salidas = [movimiento(int(generador.integers(1, 61)), int(generador.integers(1, 15)))
                   for _ in range(150)]
        ventana, cobertura = 30, 21

        filas = {f["id"]: f for f in rs.prediccion_reposicion(productos, salidas, ventana, cobertura)["productos"]}
        for p in productos:
            vendidas = sum(m.cantidad for m in salidas if m.id_producto == p.id)
            diario = round(vendidas / ventana, 2)
            dias = int(p.cantidad / diario) if diario > 0 else None
            sugerido = (max(0, ceil(diario * cobertura - p.cantidad)) if diario > 0
                        else max(0, p.stock_minimo - p.cantidad))
            assert (filas[p.id]["consumo_diario"], filas[p.id]["dias_restantes"],
                    filas[p.id]["sugerido"]) == (diario, dias, sugerido)


class TestVencimientos:
    def test_clasifica_y_ordena(self, productos_muestra):
        datos = rs.reporte_vencimientos(productos_muestra, dias_alerta=30)
        assert [(f["nombre"], f["dias_restantes"], f["estado_venc"]) for f in datos["productos"]] == [
            ("Leche entera", -3, "VENCIDO"),
            ("Café molido", 10, "POR VENCER"),
            ("Yogurt fresa", 90, "VIGENTE"),
        ]
        assert datos["resumen"] == {
            "perecederos": 3, "vencidos": 1, "por_vencer": 1, "vigentes": 1, "unidades_riesgo": 65,
        }

    def test_respeta_los_dias_de_alerta(self, productos_muestra):
        resumen = rs.reporte_vencimientos(productos_muestra, dias_alerta=5)["resumen"]
        assert (resumen["por_vencer"], resumen["vigentes"], resumen["unidades_riesgo"]) == (0, 2, 40)

    def test_sin_perecederos(self):
        datos = rs.reporte_vencimientos([producto()])
        assert datos["productos"] == []
        assert datos["resumen"]["perecederos"] == 0


class TestMovimientos:
    def test_resumen_movimientos(self):
        movimientos = [movimiento(1, 5, "SALIDA"), movimiento(1, 10, "ENTRADA", precio=2.0),
                       movimiento(1, 3, "AJUSTE")]
        assert rs.resumen_movimientos(movimientos) == {
            "total": 3, "entradas": 1, "salidas": 1, "ajustes": 1,
            "unidades_entrada": 10, "unidades_salida": 5, "valor_comprado": 20.0,
        }

    def test_por_mes_cubre_los_ultimos_meses(self):
        movimientos = [movimiento(1, 4, "ENTRADA", hace_dias=0, precio=1),
                       movimiento(1, 2, "SALIDA", hace_dias=0),
                       movimiento(1, 9, "SALIDA", hace_dias=400),
                       movimiento(1, 7, "AJUSTE", hace_dias=0)]
        datos = rs.movimientos_por_mes(movimientos, meses=6)
        assert len(datos["meses"]) == 6
        assert datos["meses"][-1] == date.today().strftime("%Y-%m")
        assert (datos["entradas"][-1], datos["salidas"][-1]) == (4, 2)
        assert sum(datos["salidas"]) == 2

    def test_por_mes_sin_movimientos(self):
        datos = rs.movimientos_por_mes([], meses=3)
        assert datos["entradas"] == [0, 0, 0]

    def test_compras_por_proveedor(self):
        movimientos = [
            movimiento(1, 10, "ENTRADA", proveedor="Distribuidora SAC", precio=2300),
            movimiento(4, 20, "ENTRADA", proveedor="Distribuidora SAC", precio=4.1),
            movimiento(2, 50, "ENTRADA", proveedor="Importaciones EIRL", precio=45.5),
            movimiento(7, 100, "ENTRADA", proveedor=None, precio=0.9),
            movimiento(1, 3, "SALIDA"),
        ]
        datos = rs.compras_por_proveedor(movimientos)
        assert datos["por_proveedor"] == [
            {"proveedor": "Distribuidora SAC", "movimientos": 2, "unidades": 30, "total": 23082.0},
            {"proveedor": "Importaciones EIRL", "movimientos": 1, "unidades": 50, "total": 2275.0},
            {"proveedor": "—", "movimientos": 1, "unidades": 100, "total": 90.0},
        ]
        assert datos["resumen"]["entradas"] == 4

    def test_compras_sin_entradas(self):
        assert rs.compras_por_proveedor([movimiento(1, 1)])["por_proveedor"] == []
