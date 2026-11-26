from models.perfil import crear_perfil
from repositories.perfil_repository import PerfilRepository
from repositories.modulo_repository import ModuloRepository
from exceptions.errores import PerfilNoEncontradoError, DatosInvalidosError

RUTA_GESTION = "perfiles"
MENSAJE_PERFIL_SISTEMA = "El perfil Administrador es del sistema y no se puede {accion}."


class PerfilService:
    """Reglas de negocio de perfiles."""

    def __init__(self, repositorio=None, modulo_repo=None):
        self.repositorio = repositorio or PerfilRepository()
        self.modulo_repo = modulo_repo or ModuloRepository()

    def listar_perfiles(self, solo_activos=False):
        """Lista los perfiles; con solo_activos=True, solo los activos."""
        return self.repositorio.listar(solo_activos)

    def obtener_perfil(self, id_perfil):
        """Devuelve el perfil o lanza un error 404 si no existe."""
        perfil = self.repositorio.obtener(id_perfil)
        if perfil is None:
            raise PerfilNoEncontradoError(f"No existe el perfil con id {id_perfil}.")
        return perfil

    def crear_perfil(self, datos):
        """Valida los datos y registra un perfil nuevo."""
        perfil = crear_perfil(dict(datos))
        if self.repositorio.buscar_por_nombre(perfil.nombre):
            raise DatosInvalidosError("Ya existe un perfil con ese nombre.")
        return self.repositorio.agregar(perfil)

    def actualizar_perfil(self, id_perfil, datos):
        """Valida los datos y actualiza el perfil; el perfil Administrador no se edita."""
        if self.obtener_perfil(id_perfil).es_sistema:
            raise DatosInvalidosError(MENSAJE_PERFIL_SISTEMA.format(accion="modificar"))
        datos = dict(datos)
        datos["id_perfil"] = id_perfil
        perfil = crear_perfil(datos)

        existente = self.repositorio.buscar_por_nombre(perfil.nombre)
        if existente and existente.id_perfil != id_perfil:
            raise DatosInvalidosError("Ya existe otro perfil con ese nombre.")

        id_gestion = self._id_modulo_gestion()
        if id_gestion is not None and id_gestion not in perfil.modulos:
            if not self._otros_gestionan(id_perfil, id_gestion):
                raise DatosInvalidosError(
                    "No puedes quitar el módulo 'Perfiles': debe quedar al menos "
                    "un perfil activo que pueda gestionar los módulos."
                )
        return self.repositorio.actualizar(perfil)

    def eliminar_perfil(self, id_perfil):
        """Elimina el perfil, salvo el perfil Administrador."""
        if self.obtener_perfil(id_perfil).es_sistema:
            raise DatosInvalidosError(MENSAJE_PERFIL_SISTEMA.format(accion="eliminar"))
        self.repositorio.eliminar(id_perfil)

    def cambiar_estado_perfil(self, id_perfil, estado):
        """Activa o desactiva el perfil; el perfil Administrador no cambia de estado."""
        if int(estado) not in (0, 1):
            raise DatosInvalidosError("Estado inválido.")
        if self.obtener_perfil(id_perfil).es_sistema:
            raise DatosInvalidosError(MENSAJE_PERFIL_SISTEMA.format(accion="desactivar"))
        self.repositorio.cambiar_estado(id_perfil, estado)

    def _id_modulo_gestion(self):
        for modulo in self.modulo_repo.listar_todos():
            if modulo.ruta == RUTA_GESTION:
                return modulo.id_modulo
        return None

    def _otros_gestionan(self, id_perfil, id_gestion):
        return any(
            p.id_perfil != id_perfil and id_gestion in p.modulos
            for p in self.repositorio.listar(solo_activos=True)
        )
