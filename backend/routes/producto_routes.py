from flask import Blueprint, request

from controllers.producto_controller import ProductoController
from sesion import login_requerido, requiere_modulo

producto_bp = Blueprint("productos", __name__, url_prefix="/api/productos")
controller = ProductoController()


@producto_bp.route("/opciones", methods=["GET"])
@login_requerido
def opciones():
    """GET /api/productos/opciones: los productos activos para selectores."""
    return controller.opciones()


@producto_bp.route("", methods=["GET"])
@requiere_modulo("productos")
def listar():
    """GET /api/productos: lista los productos."""
    return controller.listar()


@producto_bp.route("", methods=["POST"])
@requiere_modulo("productos")
def crear():
    """POST /api/productos: crea un producto."""
    return controller.crear(request.get_json(silent=True) or {})


@producto_bp.route("/importar", methods=["POST"])
@requiere_modulo("productos")
def importar():
    """POST /api/productos/importar: carga productos desde CSV o JSON."""
    return controller.importar(request.files.get("archivo"))


@producto_bp.route("/<int:id>", methods=["PUT"])
@requiere_modulo("productos")
def actualizar(id):
    """PUT /api/productos/<int:id>: actualiza un producto."""
    return controller.actualizar(id, request.get_json(silent=True) or {})


@producto_bp.route("/<int:id>", methods=["DELETE"])
@requiere_modulo("productos")
def eliminar(id):
    """DELETE /api/productos/<int:id>: elimina un producto (eliminación lógica)."""
    return controller.eliminar(id)


@producto_bp.route("/<int:id>/estado", methods=["PUT"])
@requiere_modulo("productos")
def cambiar_estado(id):
    """PUT /api/productos/<int:id>/estado: activa o desactiva un producto."""
    return controller.cambiar_estado(id, request.get_json(silent=True) or {})
