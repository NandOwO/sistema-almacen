import threading


class Singleton(type):
    """Metaclase que garantiza una única instancia por clase, segura entre hilos."""

    _instancias = {}
    _candado = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instancias:
            with cls._candado:
                if cls not in cls._instancias:
                    cls._instancias[cls] = super().__call__(*args, **kwargs)
        return cls._instancias[cls]

    def reiniciar(cls):
        """Descarta la instancia actual; la siguiente llamada crea una nueva."""
        with cls._candado:
            cls._instancias.pop(cls, None)
