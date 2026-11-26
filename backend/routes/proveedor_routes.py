from flask import Blueprint, request

from controllers.proveedor_controller import ProveedorController
from sesion import login_requerido, requiere_modulo

proveedor_bp = Blueprint("proveedores", __name__, url_prefix="/api/proveedores")
controller = ProveedorController()


@proveedor_bp.route("/opciones", methods=["GET"])
@login_requerido
def opciones():
    """GET /api/proveedores/opciones: los proveedores activos para selectores."""
    return controller.opciones()


@proveedor_bp.route("", methods=["GET"])
@requiere_modulo("proveedores")
def listar():
    """GET /api/proveedores: lista los proveedores."""
    return controller.listar()


@proveedor_bp.route("", methods=["POST"])
@requiere_modulo("proveedores")
def crear():
    """POST /api/proveedores: crea un proveedor."""
    return controller.crear(request.get_json(silent=True) or {})


@proveedor_bp.route("/<int:id_proveedor>", methods=["PUT"])
@requiere_modulo("proveedores")
def actualizar(id_proveedor):
    """PUT /api/proveedores/<int:id_proveedor>: actualiza un proveedor."""
    return controller.actualizar(id_proveedor, request.get_json(silent=True) or {})


@proveedor_bp.route("/<int:id_proveedor>", methods=["DELETE"])
@requiere_modulo("proveedores")
def eliminar(id_proveedor):
    """DELETE /api/proveedores/<int:id_proveedor>: elimina un proveedor (eliminación lógica)."""
    return controller.eliminar(id_proveedor)


@proveedor_bp.route("/<int:id_proveedor>/estado", methods=["PUT"])
@requiere_modulo("proveedores")
def cambiar_estado(id_proveedor):
    """PUT /api/proveedores/<int:id_proveedor>/estado: activa o desactiva un proveedor."""
    return controller.cambiar_estado(id_proveedor, request.get_json(silent=True) or {})
