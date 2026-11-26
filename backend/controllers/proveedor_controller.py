from flask import jsonify

from services.proveedor_service import ProveedorService


class ProveedorController:
    """Traduce las peticiones HTTP de proveedores en llamadas al servicio."""

    def __init__(self):
        self.service = ProveedorService()

    def listar(self):
        """Responde con los proveedores en JSON."""
        return jsonify([p.to_dict() for p in self.service.listar_proveedores()])

    def opciones(self):
        """Responde con los proveedores activos, para las listas desplegables."""
        activos = self.service.listar_proveedores(solo_activos=True)
        return jsonify([p.to_dict() for p in activos])

    def crear(self, datos):
        """Crea un proveedor y responde 201 con sus datos."""
        return jsonify(self.service.crear_proveedor(datos).to_dict()), 201

    def actualizar(self, id_proveedor, datos):
        """Actualiza el proveedor y responde con sus datos."""
        return jsonify(self.service.actualizar_proveedor(id_proveedor, datos).to_dict())

    def eliminar(self, id_proveedor):
        """Elimina el proveedor y responde con un mensaje."""
        self.service.eliminar_proveedor(id_proveedor)
        return jsonify({"mensaje": "Proveedor eliminado."})

    def cambiar_estado(self, id_proveedor, datos):
        """Cambia el estado del proveedor y responde con el nuevo valor."""
        estado = int(datos.get("estado", 1))
        self.service.cambiar_estado_proveedor(id_proveedor, estado)
        return jsonify({"mensaje": "Estado actualizado.", "estado": estado})
