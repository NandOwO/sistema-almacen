from repositories.database import get_connection
from models.proveedor import crear_proveedor


class ProveedorRepository:
    """Acceso a datos de proveedores en MySQL."""

    def _fila_a_proveedor(self, fila):
        return crear_proveedor(dict(fila))

    def listar(self, solo_activos=False):
        """Lista los proveedores no eliminados; con solo_activos=True, solo los activos."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            filtro = " WHERE estado = 1" if solo_activos else " WHERE estado <> 2"
            cursor.execute("SELECT * FROM proveedores" + filtro + " ORDER BY nombre_proveedor")
            return [self._fila_a_proveedor(f) for f in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def obtener(self, id_proveedor):
        """Busca un proveedor por id; devuelve None si no existe."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM proveedores WHERE id_proveedor = %s", (id_proveedor,)
            )
            fila = cursor.fetchone()
            return self._fila_a_proveedor(fila) if fila else None
        finally:
            cursor.close()
            conn.close()

    def buscar_por_ruc(self, ruc):
        """Busca un proveedor por RUC; devuelve None si no existe."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM proveedores WHERE ruc = %s AND estado <> 2", (ruc,)
            )
            fila = cursor.fetchone()
            return self._fila_a_proveedor(fila) if fila else None
        finally:
            cursor.close()
            conn.close()

    def agregar(self, proveedor):
        """Inserta el proveedor y le asigna el id generado."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO proveedores
                   (nombre_proveedor, ruc, representante, telefono, correo, direccion, estado)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    proveedor.nombre_proveedor,
                    proveedor.ruc,
                    proveedor.representante,
                    proveedor.telefono,
                    proveedor.correo,
                    proveedor.direccion,
                    proveedor.estado,
                ),
            )
            conn.commit()
            proveedor.id_proveedor = cursor.lastrowid
            return proveedor
        finally:
            cursor.close()
            conn.close()

    def actualizar(self, proveedor):
        """Actualiza el proveedor en la base de datos."""
        conn = get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """UPDATE proveedores SET
                   nombre_proveedor = %s, ruc = %s, representante = %s,
                   telefono = %s, correo = %s, direccion = %s
                   WHERE id_proveedor = %s""",
                (
                    proveedor.nombre_proveedor,
                    proveedor.ruc,
                    proveedor.representante,
                    proveedor.telefono,
                    proveedor.correo,
                    proveedor.direccion,
                    proveedor.id_proveedor,
                ),
            )
            conn.commit()
            return proveedor
        finally:
            cursor.close()
            conn.close()

    def eliminar(self, id_proveedor):
        """Marca el proveedor como eliminado (eliminación lógica)."""
        self.cambiar_estado(id_proveedor, 2)

    def cambiar_estado(self, id_proveedor, estado):
        """Actualiza el estado (0 inactivo, 1 activo, 2 eliminado)."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE proveedores SET estado = %s WHERE id_proveedor = %s",
                (int(estado), id_proveedor),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
