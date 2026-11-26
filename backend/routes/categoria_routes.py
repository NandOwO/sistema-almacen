from flask import Blueprint, request

from controllers.categoria_controller import CategoriaController
from sesion import login_requerido, requiere_modulo

categoria_bp = Blueprint("categorias", __name__, url_prefix="/api/categorias")
controller = CategoriaController()


@categoria_bp.route("/opciones", methods=["GET"])
@login_requerido
def opciones():
    """GET /api/categorias/opciones: las categorías activas para selectores."""
    return controller.opciones()


@categoria_bp.route("", methods=["GET"])
@requiere_modulo("categorias")
def listar():
    """GET /api/categorias: lista las categorías."""
    return controller.listar()


@categoria_bp.route("", methods=["POST"])
@requiere_modulo("categorias")
def crear():
    """POST /api/categorias: crea una categoría."""
    return controller.crear(request.get_json(silent=True) or {})


@categoria_bp.route("/<int:id>", methods=["PUT"])
@requiere_modulo("categorias")
def actualizar(id):
    """PUT /api/categorias/<int:id>: actualiza una categoría."""
    return controller.actualizar(id, request.get_json(silent=True) or {})


@categoria_bp.route("/<int:id>", methods=["DELETE"])
@requiere_modulo("categorias")
def eliminar(id):
    """DELETE /api/categorias/<int:id>: elimina una categoría (eliminación lógica)."""
    return controller.eliminar(id)


@categoria_bp.route("/<int:id>/estado", methods=["PUT"])
@requiere_modulo("categorias")
def cambiar_estado(id):
    """PUT /api/categorias/<int:id>/estado: activa o desactiva una categoría."""
    return controller.cambiar_estado(id, request.get_json(silent=True) or {})
