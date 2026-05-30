"""Configuración de bitácora para la aplicación."""

import logging


def configure_logger() -> None:
    """
    Configura el sistema de logging de la aplicación.

    Returns:
        None.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
