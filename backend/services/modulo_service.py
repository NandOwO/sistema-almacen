from repositories.modulo_repository import ModuloRepository


class ModuloService:
    """Consulta de los módulos del menú."""

    def __init__(self, repositorio=None):
        self.repositorio = repositorio or ModuloRepository()

    def menu_de_perfil(self, id_perfil):
        """Módulos visibles para el perfil; lista vacía si no hay perfil."""
        if not id_perfil:
            return []
        return self.repositorio.listar_por_perfil(id_perfil)

    def listar_todos(self):
        """Todos los módulos activos."""
        return self.repositorio.listar_todos()
