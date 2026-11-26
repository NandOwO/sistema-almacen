from flask import jsonify

from services.auth_service import AuthService
from services.usuario_service import UsuarioService
from exceptions.errores import NoAutenticadoError
from sesion import iniciar_sesion, cerrar_sesion, id_usuario_actual, hay_sesion


class AuthController:
    """Inicio y cierre de sesión y datos del usuario conectado."""

    def __init__(self):
        self.service = AuthService()
        self.usuarios = UsuarioService()

    def login(self, datos):
        """Autentica al usuario y abre su sesión."""
        usuario = self.service.autenticar(datos.get("usuario"), datos.get("clave"))
        iniciar_sesion(usuario)
        return jsonify(usuario.to_dict())

    def logout(self):
        """Cierra la sesión actual."""
        cerrar_sesion()
        return jsonify({"mensaje": "Sesión cerrada."})

    def usuario_actual(self):
        """Responde con el usuario de la sesión activa."""
        if not hay_sesion():
            raise NoAutenticadoError("No hay una sesión activa.")
        usuario = self.service.obtener(id_usuario_actual())
        if usuario is None:
            cerrar_sesion()
            raise NoAutenticadoError("La sesión ya no es válida.")
        return jsonify(usuario.to_dict())

    def actualizar_mis_datos(self, datos):
        """Actualiza el nombre y el correo del usuario conectado."""
        usuario = self.usuarios.actualizar_datos_propios(id_usuario_actual(), datos)
        return jsonify(usuario.to_dict())

    def cambiar_mi_clave(self, datos):
        """Cambia la contraseña del usuario conectado."""
        self.usuarios.cambiar_clave_propia(
            id_usuario_actual(), datos.get("clave_actual"), datos.get("clave_nueva")
        )
        return jsonify({"mensaje": "Contraseña actualizada."})
