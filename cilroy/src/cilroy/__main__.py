"""Main script.

This module provides basic CLI entrypoint.

"""
import asyncio
import logging
from asyncio import FIRST_EXCEPTION
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Dict, Optional

import typer
from platformdirs import user_cache_dir
from typer import FileText

from cilroy.config import get_config
from cilroy.controller import CilroyController
from cilroy.server import CilroyServer

cli = typer.Typer()  # this is actually callable and thus can be an entry point

DEFAULT_STATE_DIRECTORY = (
    Path(user_cache_dir("kilroybot")) / "cilroy" / "state"
)


class Verbosity(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def get_logger(verbosity: Verbosity) -> Logger:
    logging.basicConfig()
    logger = logging.getLogger("cilroy")
    logger.setLevel(verbosity.value)
    return logger


async def load_or_init(
    controller: CilroyController, state_dir: Path, logger: Logger
) -> None:
    if not state_dir.exists() or not any(state_dir.iterdir()):
        logger.info("Initializing controller...")
        await controller.init()
        logger.info("Initialization complete.")
        return

    try:
        logger.info("Loading state...")
        await controller.load_saved(state_dir)
        logger.info("Loading complete.")
    except Exception as e:
        logger.warning(
            "Can't load saved state. Will try to initialize instead.",
            exc_info=e,
        )
        logger.info("Initializing controller...")
        await controller.init()
        logger.info("Initialization complete.")


async def run(config: Dict, logger: Logger, state_dir: Path) -> None:

    face = await CilroyController.build(**config.get("controllerParams", {}))
    server = CilroyServer(face, logger)

    server_task = asyncio.create_task(
        server.run(**config.get("serverParams", {}))
    )
    init_task = asyncio.create_task(load_or_init(face, state_dir, logger))

    tasks = [server_task, init_task]

    try:
        done, pending = await asyncio.wait(tasks, return_when=FIRST_EXCEPTION)
    except asyncio.CancelledError:
        done, pending = [], tasks

    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    for task in done:
        task.result()

    if (
        init_task.done()
        and not init_task.cancelled()
        and init_task.exception() is None
    ):
        logger.info("Saving state...")
        await face.save(state_dir)

        logger.info("Cleaning up...")
        await face.cleanup()


@cli.command()
def main(
    config: Optional[FileText] = typer.Option(
        None, "--config", "-c", dir_okay=False, help="Configuration file"
    ),
    verbosity: Verbosity = typer.Option(
        "INFO", "--verbosity", "-v", help="Verbosity level."
    ),
    state_directory: Optional[Path] = typer.Option(
        DEFAULT_STATE_DIRECTORY,
        "--state-directory",
        "-s",
        file_okay=False,
        writable=True,
        help="Path to state directory.",
    ),
) -> None:
    """Command line interface for cilroy."""

    config = get_config(config)
    logger = get_logger(verbosity)

    asyncio.run(run(config, logger, state_directory))


if __name__ == "__main__":
    # entry point for "python -m"
    cli()
