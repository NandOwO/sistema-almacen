import pytest

from exceptions.errores import DatosInvalidosError
from models.perfil import NOMBRE_PERFIL_ADMIN, Perfil
from models.usuario import crear_usuario
from services.perfil_service import PerfilService
from services.usuario_service import UsuarioService

ID_ADMIN, ID_VENDEDOR = 1, 2


class PerfilRepoFalso:
    def __init__(self):
        self.perfiles = {
            ID_ADMIN: Perfil(ID_ADMIN, NOMBRE_PERFIL_ADMIN, modulos=[1, 2, 3]),
            ID_VENDEDOR: Perfil(ID_VENDEDOR, "Vendedor", modulos=[1, 3]),
        }
        self.cambios = []

    def obtener(self, id_perfil):
        return self.perfiles.get(id_perfil)

    def listar(self, solo_activos=False):
        return list(self.perfiles.values())

    def buscar_por_nombre(self, nombre):
        return next((p for p in self.perfiles.values() if p.nombre.lower() == nombre.lower()), None)

    def actualizar(self, perfil):
        self.cambios.append(("actualizar", perfil.id_perfil))
        return perfil

    def eliminar(self, id_perfil):
        self.cambios.append(("eliminar", id_perfil))

    def cambiar_estado(self, id_perfil, estado):
        self.cambios.append(("estado", id_perfil))


class ModuloRepoFalso:
    def listar_todos(self):
        return []


class UsuarioRepoFalso:
    def __init__(self, usuarios):
        self.usuarios = {u.id_usuario: u for u in usuarios}

    def obtener(self, id_usuario):
        return self.usuarios.get(id_usuario)

    def listar(self, solo_activos=False):
        return [u for u in self.usuarios.values() if u.estado == 1 or not solo_activos]

    def buscar_por_usuario(self, nombre):
        return next((u for u in self.usuarios.values() if u.usuario == nombre), None)

    def agregar(self, usuario, clave_hash):
        usuario.id_usuario = max(self.usuarios, default=0) + 1
        self.usuarios[usuario.id_usuario] = usuario
        return usuario

    def actualizar(self, usuario, clave_hash):
        self.usuarios[usuario.id_usuario] = usuario
        return usuario


def usuario(id_usuario, nombre, id_perfil, estado=1):
    return crear_usuario({"id_usuario": id_usuario, "usuario": nombre, "nombre": "Persona Prueba",
                          "id_perfil": id_perfil, "estado": estado})


@pytest.fixture
def perfiles():
    return PerfilService(repositorio=PerfilRepoFalso(), modulo_repo=ModuloRepoFalso())


def servicio_usuarios(*usuarios):
    return UsuarioService(repositorio=UsuarioRepoFalso(usuarios), perfil_repo=PerfilRepoFalso())


class TestPerfilAdministrador:
    def test_se_identifica_como_perfil_del_sistema(self):
        assert Perfil(1, "administrador").es_sistema is True
        assert Perfil(2, "Vendedor").es_sistema is False
        assert Perfil(1, NOMBRE_PERFIL_ADMIN).to_dict()["es_sistema"] is True

    @pytest.mark.parametrize("operacion", [
        lambda s: s.actualizar_perfil(ID_ADMIN, {"nombre": NOMBRE_PERFIL_ADMIN, "modulos": [1]}),
        lambda s: s.cambiar_estado_perfil(ID_ADMIN, 0),
        lambda s: s.eliminar_perfil(ID_ADMIN),
    ])
    def test_no_se_puede_modificar(self, perfiles, operacion):
        with pytest.raises(DatosInvalidosError, match="es del sistema"):
            operacion(perfiles)
        assert perfiles.repositorio.cambios == []

    def test_otros_perfiles_si_se_pueden_modificar(self, perfiles):
        perfiles.actualizar_perfil(ID_VENDEDOR, {"nombre": "Vendedor", "modulos": [1]})
        perfiles.cambiar_estado_perfil(ID_VENDEDOR, 0)
        perfiles.eliminar_perfil(ID_VENDEDOR)
        assert [c[0] for c in perfiles.repositorio.cambios] == ["actualizar", "estado", "eliminar"]

    def test_no_se_puede_crear_otro_con_el_mismo_nombre(self, perfiles):
        with pytest.raises(DatosInvalidosError, match="Ya existe"):
            perfiles.crear_perfil({"nombre": "ADMINISTRADOR", "modulos": [1]})


class TestAsignacionDelRolAdministrador:
    def test_crear_administrador_exige_confirmacion(self):
        servicio = servicio_usuarios()
        datos = {"usuario": "jefa.tienda", "clave": "segura123", "id_perfil": ID_ADMIN}
        with pytest.raises(DatosInvalidosError, match="confirme la operación"):
            servicio.crear_usuario(datos)
        assert servicio.crear_usuario(dict(datos, confirmar_admin=True)).id_perfil == ID_ADMIN

    def test_promover_a_administrador_exige_confirmacion(self):
        servicio = servicio_usuarios(usuario(1, "admin", ID_ADMIN), usuario(2, "caja01", ID_VENDEDOR))
        datos = {"usuario": "caja01", "id_perfil": ID_ADMIN, "estado": 1}
        with pytest.raises(DatosInvalidosError, match="confirme la operación"):
            servicio.actualizar_usuario(2, datos)
        assert servicio.actualizar_usuario(2, dict(datos, confirmar_admin=True)).id_perfil == ID_ADMIN

    def test_editar_un_administrador_sin_cambiar_su_rol_no_pide_confirmacion(self):
        servicio = servicio_usuarios(usuario(1, "admin", ID_ADMIN))
        editado = servicio.actualizar_usuario(1, {"usuario": "admin", "nombre": "Nuevo Nombre",
                                                  "id_perfil": ID_ADMIN, "estado": 1})
        assert editado.nombre == "Nuevo Nombre"

    def test_otros_perfiles_no_piden_confirmacion(self):
        servicio = servicio_usuarios()
        creado = servicio.crear_usuario({"usuario": "caja02", "clave": "segura123", "id_perfil": ID_VENDEDOR})
        assert creado.id_perfil == ID_VENDEDOR

    @pytest.mark.parametrize("cambio", [{"id_perfil": ID_VENDEDOR}, {"estado": 0}])
    def test_no_se_puede_dejar_el_sistema_sin_administrador(self, cambio):
        servicio = servicio_usuarios(usuario(1, "admin", ID_ADMIN), usuario(2, "caja01", ID_VENDEDOR))
        datos = dict({"usuario": "admin", "id_perfil": ID_ADMIN, "estado": 1}, **cambio)
        with pytest.raises(DatosInvalidosError, match="único administrador"):
            servicio.actualizar_usuario(1, datos)

    def test_se_puede_quitar_el_rol_si_queda_otro_administrador(self):
        servicio = servicio_usuarios(usuario(1, "admin", ID_ADMIN), usuario(2, "jefa", ID_ADMIN))
        editado = servicio.actualizar_usuario(2, {"usuario": "jefa", "id_perfil": ID_VENDEDOR, "estado": 1})
        assert editado.id_perfil == ID_VENDEDOR
