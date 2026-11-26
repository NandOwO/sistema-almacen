from flask import jsonify

from services.categoria_service import CategoriaService


class CategoriaController:
    """Traduce las peticiones HTTP de categorías en llamadas al servicio."""

    def __init__(self):
        self.service = CategoriaService()

    def listar(self):
        """Responde con las categorías en JSON."""
        return jsonify([c.to_dict() for c in self.service.listar_categorias()])

    def opciones(self):
        """Responde con las categorías activas, para las listas desplegables."""
        activas = self.service.listar_categorias(solo_activos=True)
        return jsonify([c.to_dict() for c in activas])

    def crear(self, datos):
        """Crea una categoría y responde 201 con sus datos."""
        return jsonify(self.service.crear_categoria(datos).to_dict()), 201

    def actualizar(self, id, datos):
        """Actualiza la categoría y responde con sus datos."""
        return jsonify(self.service.actualizar_categoria(id, datos).to_dict())

    def eliminar(self, id):
        """Elimina la categoría y responde con un mensaje."""
        self.service.eliminar_categoria(id)
        return jsonify({"mensaje": "Categoría eliminada."})

    def cambiar_estado(self, id, datos):
        """Cambia el estado de la categoría y responde con el nuevo valor."""
        estado = int(datos.get("estado", 1))
        self.service.cambiar_estado_categoria(id, estado)
        return jsonify({"mensaje": "Estado actualizado.", "estado": estado})
