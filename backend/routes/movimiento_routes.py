from flask import Blueprint, request

from controllers.movimiento_controller import MovimientoController
from sesion import requiere_modulo

movimiento_bp = Blueprint("movimientos", __name__, url_prefix="/api/movimientos")
controller = MovimientoController()


@movimiento_bp.route("", methods=["GET"])
@requiere_modulo("inventario")
def listar():
    """GET /api/movimientos: kardex con filtros opcionales."""
    filtros = {
        "id_producto": request.args.get("producto"),
        "tipo_movimiento": request.args.get("tipo"),
    }
    return controller.listar(filtros)


@movimiento_bp.route("", methods=["POST"])
@requiere_modulo("inventario")
def registrar():
    """POST /api/movimientos: registra una entrada, salida o ajuste."""
    return controller.registrar(request.get_json(silent=True) or {})
