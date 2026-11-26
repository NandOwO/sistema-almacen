from flask import jsonify

from services.perfil_service import PerfilService


class PerfilController:
    """Traduce las peticiones HTTP de perfiles en llamadas al servicio."""

    def __init__(self):
        self.service = PerfilService()

    def listar(self):
        """Responde con los perfiles en JSON."""
        return jsonify([p.to_dict() for p in self.service.listar_perfiles()])

    def opciones(self):
        """Responde con los perfiles activos, para las listas desplegables."""
        activos = self.service.listar_perfiles(solo_activos=True)
        return jsonify([p.to_dict() for p in activos])

    def crear(self, datos):
        """Crea un perfil y responde 201 con sus datos."""
        return jsonify(self.service.crear_perfil(datos).to_dict()), 201

    def actualizar(self, id_perfil, datos):
        """Actualiza el perfil y responde con sus datos."""
        return jsonify(self.service.actualizar_perfil(id_perfil, datos).to_dict())

    def eliminar(self, id_perfil):
        """Elimina el perfil y responde con un mensaje."""
        self.service.eliminar_perfil(id_perfil)
        return jsonify({"mensaje": "Perfil eliminado."})

    def cambiar_estado(self, id_perfil, datos):
        """Cambia el estado del perfil y responde con el nuevo valor."""
        estado = int(datos.get("estado", 1))
        self.service.cambiar_estado_perfil(id_perfil, estado)
        return jsonify({"mensaje": "Estado actualizado.", "estado": estado})
