class InventarioError(Exception):
    """Error base del dominio; cada subclase define su código HTTP."""
    codigo_http = 400


class ProductoNoEncontradoError(InventarioError):
    """El producto solicitado no existe (404)."""
    codigo_http = 404


class DatosInvalidosError(InventarioError):
    """Los datos enviados no cumplen las reglas de validación (400)."""
    codigo_http = 400


class StockInsuficienteError(InventarioError):
    """La salida supera el stock disponible (409)."""
    codigo_http = 409


class CategoriaNoEncontradaError(InventarioError):
    """La categoría solicitada no existe (404)."""
    codigo_http = 404


class ProveedorNoEncontradoError(InventarioError):
    """El proveedor solicitado no existe (404)."""
    codigo_http = 404


class PerfilNoEncontradoError(InventarioError):
    """El perfil solicitado no existe (404)."""
    codigo_http = 404


class UsuarioNoEncontradoError(InventarioError):
    """El usuario solicitado no existe (404)."""
    codigo_http = 404


class CredencialesInvalidasError(InventarioError):
    """Usuario o contraseña incorrectos (401)."""
    codigo_http = 401


class NoAutenticadoError(InventarioError):
    """La petición requiere una sesión iniciada (401)."""
    codigo_http = 401


class NoAutorizadoError(InventarioError):
    """El perfil no tiene permiso para el módulo (403)."""
    codigo_http = 403
