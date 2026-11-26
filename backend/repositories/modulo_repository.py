from repositories.database import get_connection
from models.modulo import crear_modulo


class ModuloRepository:
    """Acceso a datos de módulos en MySQL."""

    def _fila_a_modulo(self, fila):
        return crear_modulo(dict(fila))

    def listar_por_perfil(self, id_perfil):
        """Módulos activos asignados a un perfil, en orden de menú."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT m.* FROM modulos m
                   JOIN perfil_modulo pm ON pm.id_modulo = m.id_modulo
                   WHERE pm.id_perfil = %s AND m.estado = 1
                   ORDER BY m.orden, m.id_modulo""",
                (id_perfil,),
            )
            return [self._fila_a_modulo(f) for f in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def listar_todos(self):
        """Todos los módulos activos, en orden de menú."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM modulos ORDER BY orden, id_modulo")
            return [self._fila_a_modulo(f) for f in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def rutas_de_perfil(self, id_perfil):
        """Conjunto de rutas a las que un perfil tiene acceso."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT m.ruta FROM modulos m
                   JOIN perfil_modulo pm ON pm.id_modulo = m.id_modulo
                   WHERE pm.id_perfil = %s AND m.estado = 1""",
                (id_perfil,),
            )
            return {fila["ruta"] for fila in cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()
