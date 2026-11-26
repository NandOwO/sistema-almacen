from werkzeug.security import generate_password_hash, check_password_hash

from models.usuario import crear_usuario
from repositories.usuario_repository import UsuarioRepository
from repositories.perfil_repository import PerfilRepository
from exceptions.errores import (
    UsuarioNoEncontradoError, DatosInvalidosError, CredencialesInvalidasError,
)

LONGITUD_MINIMA_CLAVE = 4
MENSAJE_CONFIRMAR_ADMIN = (
    "Asignar el rol Administrador da acceso a todo el sistema: confirme la operación."
)


class UsuarioService:
    """Reglas de negocio de usuarios."""

    def __init__(self, repositorio=None, perfil_repo=None):
        self.repositorio = repositorio or UsuarioRepository()
        self.perfil_repo = perfil_repo or PerfilRepository()

    def listar_usuarios(self, solo_activos=False):
        """Lista los usuarios; con solo_activos=True, solo los activos."""
        return self.repositorio.listar(solo_activos)

    def obtener_usuario(self, id_usuario):
        """Devuelve el usuario o lanza un error 404 si no existe."""
        usuario = self.repositorio.obtener(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(f"No existe el usuario con id {id_usuario}.")
        return usuario

    def crear_usuario(self, datos):
        """Valida los datos y registra un usuario nuevo."""
        usuario = crear_usuario(dict(datos))
        self._validar_perfil(usuario.id_perfil)
        self._exigir_confirmacion_admin(usuario.id_perfil, None, datos)
        clave = self._validar_clave(datos.get("clave"), obligatoria=True)
        if self.repositorio.buscar_por_usuario(usuario.usuario):
            raise DatosInvalidosError("Ya existe un usuario con ese nombre.")
        return self.repositorio.agregar(usuario, generate_password_hash(clave))

    def actualizar_usuario(self, id_usuario, datos):
        """Valida los datos y actualiza el usuario; protege el rol Administrador."""
        actual = self.obtener_usuario(id_usuario)
        datos = dict(datos)
        datos["id_usuario"] = id_usuario
        usuario = crear_usuario(datos)
        self._validar_perfil(usuario.id_perfil)
        self._exigir_confirmacion_admin(usuario.id_perfil, actual.id_perfil, datos)
        self._conservar_un_administrador(actual, usuario)

        existente = self.repositorio.buscar_por_usuario(usuario.usuario)
        if existente and existente.id_usuario != id_usuario:
            raise DatosInvalidosError("Ya existe otro usuario con ese nombre.")

        clave = (datos.get("clave") or "").strip()
        clave_hash = None
        if clave:
            clave_hash = generate_password_hash(self._validar_clave(clave))
        return self.repositorio.actualizar(usuario, clave_hash)

    def eliminar_usuario(self, id_usuario, id_usuario_actual=None):
        """Elimina el usuario, salvo el propio o un administrador."""
        usuario = self.obtener_usuario(id_usuario)
        self._impedir_sobre_si_mismo(id_usuario, id_usuario_actual,
                                     "No puedes eliminar tu propio usuario.")
        if self._es_perfil_admin(usuario.id_perfil):
            raise DatosInvalidosError("No puedes eliminar a otro usuario administrador.")
        self.repositorio.eliminar(id_usuario)

    def cambiar_estado_usuario(self, id_usuario, estado, id_usuario_actual=None):
        """Activa o desactiva el usuario, sin afectar al propio usuario."""
        if int(estado) not in (0, 1):
            raise DatosInvalidosError("Estado inválido.")
        usuario = self.obtener_usuario(id_usuario)

        if int(estado) == 0:
            self._impedir_sobre_si_mismo(id_usuario, id_usuario_actual,
                                         "No puedes desactivar tu propio usuario.")
            if self._es_perfil_admin(usuario.id_perfil):
                raise DatosInvalidosError("No puedes desactivar a otro usuario administrador.")
        self.repositorio.cambiar_estado(id_usuario, estado)

    def _es_perfil_admin(self, id_perfil):
        if not id_perfil:
            return False
        perfil = self.perfil_repo.obtener(int(id_perfil))
        return perfil is not None and perfil.es_sistema

    def _exigir_confirmacion_admin(self, id_perfil_nuevo, id_perfil_anterior, datos):
        asigna_admin = (self._es_perfil_admin(id_perfil_nuevo)
                        and not self._es_perfil_admin(id_perfil_anterior))
        if asigna_admin and datos.get("confirmar_admin") is not True:
            raise DatosInvalidosError(MENSAJE_CONFIRMAR_ADMIN)

    def _conservar_un_administrador(self, actual, nuevo):
        pierde_admin = self._es_perfil_admin(actual.id_perfil) and (
            not self._es_perfil_admin(nuevo.id_perfil) or int(nuevo.estado) != 1
        )
        if not pierde_admin:
            return
        otros = [u for u in self.repositorio.listar(solo_activos=True)
                 if u.id_usuario != actual.id_usuario and u.id_perfil == actual.id_perfil]
        if not otros:
            raise DatosInvalidosError(
                "Es el único administrador activo: asigne el rol a otro usuario antes de cambiarlo."
            )

    def actualizar_datos_propios(self, id_usuario, datos):
        """Actualiza nombre y correo sin permitir cambiar usuario ni perfil."""
        actual = self.obtener_usuario(id_usuario)
        datos_seguros = {
            "id_usuario": id_usuario,
            "usuario": actual.usuario,
            "nombre": datos.get("nombre"),
            "correo": datos.get("correo"),
            "id_perfil": actual.id_perfil,
            "estado": actual.estado,
        }
        usuario = crear_usuario(datos_seguros)
        return self.repositorio.actualizar(usuario, None)

    def cambiar_clave_propia(self, id_usuario, clave_actual, clave_nueva):
        """Cambia la contraseña tras verificar la actual."""
        usuario = self.obtener_usuario(id_usuario)
        if not check_password_hash(usuario.clave or "", clave_actual or ""):
            raise CredencialesInvalidasError("La clave actual es incorrecta.")
        nueva = self._validar_clave(clave_nueva, obligatoria=True)
        self.repositorio.actualizar_clave(id_usuario, generate_password_hash(nueva))

    def _impedir_sobre_si_mismo(self, id_usuario, id_actual, mensaje):
        if id_actual is not None and int(id_usuario) == int(id_actual):
            raise DatosInvalidosError(mensaje)

    def _validar_perfil(self, id_perfil):
        if not id_perfil or self.perfil_repo.obtener(int(id_perfil)) is None:
            raise DatosInvalidosError("El perfil seleccionado no existe.")

    def _validar_clave(self, clave, obligatoria=False):
        clave = (clave or "").strip()
        if not clave and not obligatoria:
            return clave
        if len(clave) < LONGITUD_MINIMA_CLAVE:
            raise DatosInvalidosError(
                f"La clave debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres."
            )
        return clave
