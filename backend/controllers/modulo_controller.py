from flask import jsonify

from services.modulo_service import ModuloService
from sesion import id_perfil_actual


class ModuloController:
    """Traduce las peticiones HTTP de módulos en llamadas al servicio."""

    def __init__(self):
        self.service = ModuloService()

    def menu(self):
        """Responde con los módulos del menú permitidos al perfil actual."""
        modulos = self.service.menu_de_perfil(id_perfil_actual())
        return jsonify([m.to_dict() for m in modulos])

    def listar_todos(self):
        """Responde con todos los módulos, para asignarlos a perfiles."""
        return jsonify([m.to_dict() for m in self.service.listar_todos()])
