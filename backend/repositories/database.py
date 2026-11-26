import logging

import mysql.connector
from mysql.connector import pooling

from config import DB_CONFIG
from patterns.singleton import Singleton

TAMANO_POOL = 5

logger = logging.getLogger("inventario")


class ConexionBD(metaclass=Singleton):
    """Punto único de acceso al pool de conexiones MySQL de la aplicación."""

    def __init__(self, configuracion=None, tamano=TAMANO_POOL):
        self._configuracion = configuracion or DB_CONFIG
        self._tamano = tamano
        self._pool = None

    def _crear_pool(self):
        return pooling.MySQLConnectionPool(
            pool_name="inventario_pool",
            pool_size=self._tamano,
            pool_reset_session=True,
            **self._configuracion,
        )

    def obtener_conexion(self):
        """Devuelve una conexión del pool y lo recrea si quedó inservible."""
        if self._pool is None:
            self._pool = self._crear_pool()
        try:
            conn = self._pool.get_connection()
        except mysql.connector.Error:
            self._pool = self._crear_pool()
            conn = self._pool.get_connection()

        try:
            if not conn.is_connected():
                conn.reconnect(attempts=2, delay=1)
        except mysql.connector.Error:
            logger.warning("No se pudo reconectar con la base de datos", exc_info=True)
        return conn


def get_connection():
    """Atajo para obtener una conexión del Singleton ConexionBD."""
    return ConexionBD().obtener_conexion()
