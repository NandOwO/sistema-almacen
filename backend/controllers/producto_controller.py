from flask import jsonify

from exceptions.errores import DatosInvalidosError
from services.importacion_service import ImportacionService
from services.inventario_service import InventarioService

class ProductoController:

    def __init__(self):
        self.service = InventarioService()
        self.importacion = ImportacionService(inventario=self.service)

    def listar(self):
        productos = self.service.listar_productos()
        return jsonify([p.to_dict() for p in productos])

    def opciones(self):
        productos = self.service.listar_productos(solo_activos=True)
        return jsonify([p.to_dict() for p in productos])

    def crear(self, datos):
        producto = self.service.crear_producto(datos)
        return jsonify(producto.to_dict()), 201

    def actualizar(self, id, datos):
        producto = self.service.actualizar_producto(id, datos)
        return jsonify(producto.to_dict())

    def eliminar(self, id):
        self.service.eliminar_producto(id)
        return jsonify({"mensaje": "Producto eliminado."})

    def importar(self, archivo):
        if archivo is None or not archivo.filename:
            raise DatosInvalidosError("Seleccione un archivo CSV o JSON.")
        resultado = self.importacion.importar_productos(archivo.stream, archivo.filename)
        return jsonify(resultado), 201 if resultado["importados"] else 200

    def cambiar_estado(self, id, datos):
        estado = int(datos.get("estado", 1))
        self.service.cambiar_estado_producto(id, estado)
        return jsonify({"mensaje": "Estado actualizado.", "estado": estado})
