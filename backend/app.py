import logging

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from config import FRONTEND_DIR, PUERTO, SECRET_KEY, TAMANO_MAXIMO_ARCHIVO
from exceptions.errores import InventarioError
from routes.auth_routes import auth_bp
from routes.categoria_routes import categoria_bp
from routes.modulo_routes import modulo_bp
from routes.movimiento_routes import movimiento_bp
from routes.perfil_routes import perfil_bp
from routes.producto_routes import producto_bp
from routes.proveedor_routes import proveedor_bp
from routes.reporte_routes import reporte_bp
from routes.usuario_routes import usuario_bp
from seed_data import sembrar_datos_si_vacio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("inventario")


def crear_app():
    """Crea la aplicación Flask, siembra datos iniciales y registra rutas y errores."""
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.secret_key = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = TAMANO_MAXIMO_ARCHIVO

    try:
        sembrar_datos_si_vacio()
    except Exception:
        logger.error("No se pudieron sembrar los datos iniciales", exc_info=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(modulo_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(producto_bp)
    app.register_blueprint(reporte_bp)
    app.register_blueprint(categoria_bp)
    app.register_blueprint(proveedor_bp)
    app.register_blueprint(movimiento_bp)

    @app.route("/")
    def inicio():
        """Sirve la página principal de la SPA."""
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.errorhandler(InventarioError)
    def manejar_error_dominio(error):
        """Responde los errores del dominio con su código HTTP."""
        return jsonify({"error": str(error)}), error.codigo_http

    @app.errorhandler(413)
    def archivo_muy_grande(error):
        """Responde 413 cuando el archivo supera el tamaño permitido."""
        limite = TAMANO_MAXIMO_ARCHIVO // (1024 * 1024)
        return jsonify({"error": f"El archivo supera el límite de {limite} MB."}), 413

    @app.errorhandler(HTTPException)
    def error_http(error):
        """Responde los errores HTTP (404, 405...) en JSON."""
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def error_inesperado(error):
        """Registra el error en el log y responde 500 sin exponer detalles."""
        logger.error("Error no controlado", exc_info=True)
        return jsonify({"error": "Ocurrió un error interno. Inténtalo de nuevo más tarde."}), 500

    return app


if __name__ == "__main__":
    aplicacion = crear_app()
    print(f"Servidor en http://localhost:{PUERTO}")
    aplicacion.run(host="0.0.0.0", port=PUERTO, debug=True)
