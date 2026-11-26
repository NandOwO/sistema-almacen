from flask import Blueprint, request

from controllers.auth_controller import AuthController
from sesion import login_requerido

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
controller = AuthController()


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/auth/login: inicia sesión."""
    return controller.login(request.get_json(silent=True) or {})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """POST /api/auth/logout: cierra la sesión."""
    return controller.logout()


@auth_bp.route("/actual", methods=["GET"])
def actual():
    """GET /api/auth/actual: usuario de la sesión activa."""
    return controller.usuario_actual()


@auth_bp.route("/mis-datos", methods=["PUT"])
@login_requerido
def mis_datos():
    """PUT /api/auth/mis-datos: actualiza los datos propios."""
    return controller.actualizar_mis_datos(request.get_json(silent=True) or {})


@auth_bp.route("/cambiar-clave", methods=["POST"])
@login_requerido
def cambiar_clave():
    """POST /api/auth/cambiar-clave: cambia la contraseña propia."""
    return controller.cambiar_mi_clave(request.get_json(silent=True) or {})
