from flask import Blueprint, request

from controllers.usuario_controller import UsuarioController
from sesion import requiere_modulo

usuario_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")
controller = UsuarioController()


@usuario_bp.route("", methods=["GET"])
@requiere_modulo("usuarios")
def listar():
    """GET /api/usuarios: lista los usuarios."""
    return controller.listar()


@usuario_bp.route("", methods=["POST"])
@requiere_modulo("usuarios")
def crear():
    """POST /api/usuarios: crea un usuario."""
    return controller.crear(request.get_json(silent=True) or {})


@usuario_bp.route("/<int:id_usuario>", methods=["PUT"])
@requiere_modulo("usuarios")
def actualizar(id_usuario):
    """PUT /api/usuarios/<int:id_usuario>: actualiza un usuario."""
    return controller.actualizar(id_usuario, request.get_json(silent=True) or {})


@usuario_bp.route("/<int:id_usuario>", methods=["DELETE"])
@requiere_modulo("usuarios")
def eliminar(id_usuario):
    """DELETE /api/usuarios/<int:id_usuario>: elimina un usuario (eliminación lógica)."""
    return controller.eliminar(id_usuario)


@usuario_bp.route("/<int:id_usuario>/estado", methods=["PUT"])
@requiere_modulo("usuarios")
def cambiar_estado(id_usuario):
    """PUT /api/usuarios/<int:id_usuario>/estado: activa o desactiva un usuario."""
    return controller.cambiar_estado(id_usuario, request.get_json(silent=True) or {})
