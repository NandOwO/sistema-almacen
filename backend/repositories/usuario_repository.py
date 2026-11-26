from repositories.database import get_connection
from models.usuario import crear_usuario

SELECT_BASE = (
    "SELECT u.*, pf.nombre AS perfil "
    "FROM usuarios u LEFT JOIN perfiles pf ON u.id_perfil = pf.id_perfil"
)


class UsuarioRepository:
    """Acceso a datos de usuarios en MySQL."""

    def _fila_a_usuario(self, fila):
        return crear_usuario(dict(fila))

    def listar(self, solo_activos=False):
        """Lista los usuarios no eliminados; con solo_activos=True, solo los activos."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            filtro = " WHERE u.estado = 1" if solo_activos else " WHERE u.estado <> 2"
            cursor.execute(SELECT_BASE + filtro + " ORDER BY u.usuario")
            return [self._fila_a_usuario(f) for f in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def obtener(self, id_usuario):
        """Busca un usuario por id; devuelve None si no existe."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(SELECT_BASE + " WHERE u.id_usuario = %s", (id_usuario,))
            fila = cursor.fetchone()
            return self._fila_a_usuario(fila) if fila else None
        finally:
            cursor.close()
            conn.close()

    def buscar_por_usuario(self, usuario):
        """Busca una cuenta por nombre de usuario; devuelve None si no existe."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(SELECT_BASE + " WHERE u.usuario = %s", (usuario,))
            fila = cursor.fetchone()
            return self._fila_a_usuario(fila) if fila else None
        finally:
            cursor.close()
            conn.close()

    def agregar(self, usuario, clave_hash):
        """Inserta el usuario y le asigna el id generado."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO usuarios (usuario, clave, nombre, correo, id_perfil, estado)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    usuario.usuario,
                    clave_hash,
                    usuario.nombre,
                    usuario.correo,
                    usuario.id_perfil,
                    usuario.estado,
                ),
            )
            conn.commit()
            usuario.id_usuario = cursor.lastrowid
            return usuario
        finally:
            cursor.close()
            conn.close()

    def actualizar(self, usuario, clave_hash=None):
        """Actualiza el usuario en la base de datos."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            if clave_hash:
                cursor.execute(
                    """UPDATE usuarios SET usuario = %s, clave = %s, nombre = %s,
                       correo = %s, id_perfil = %s, estado = %s WHERE id_usuario = %s""",
                    (usuario.usuario, clave_hash, usuario.nombre, usuario.correo,
                     usuario.id_perfil, usuario.estado, usuario.id_usuario),
                )
            else:
                cursor.execute(
                    """UPDATE usuarios SET usuario = %s, nombre = %s, correo = %s,
                       id_perfil = %s, estado = %s WHERE id_usuario = %s""",
                    (usuario.usuario, usuario.nombre, usuario.correo,
                     usuario.id_perfil, usuario.estado, usuario.id_usuario),
                )
            conn.commit()
            return usuario
        finally:
            cursor.close()
            conn.close()

    def eliminar(self, id_usuario):
        """Marca el usuario como eliminado (eliminación lógica)."""
        self.cambiar_estado(id_usuario, 2)

    def cambiar_estado(self, id_usuario, estado):
        """Actualiza el estado (0 inactivo, 1 activo, 2 eliminado)."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET estado = %s WHERE id_usuario = %s",
                (int(estado), id_usuario),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def actualizar_clave(self, id_usuario, clave_hash):
        """Guarda el nuevo hash de contraseña del usuario."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET clave = %s WHERE id_usuario = %s",
                (clave_hash, id_usuario),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
