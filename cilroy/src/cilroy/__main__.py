"""Main script.

This module provides basic CLI entrypoint.

"""
import asyncio
import logging
from asyncio import FIRST_EXCEPTION
from pathlib import Path
from typing import List, Optional

import typer
from typer import FileText

from cilroy import log
from cilroy.config import Config, get_config
from cilroy.controller import CilroyController
from cilroy.server import CilroyServer

cli = typer.Typer()  # this is actually callable and thus can be an entry point

logger = logging.getLogger(__name__)


async def load_or_init(controller: CilroyController, state_dir: Path) -> None:
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


async def run(config: Config) -> None:

    face = await CilroyController.build(**config.controller.dict())
    server = CilroyServer(face, logger)

    server_task = asyncio.create_task(server.run(**config.server.dict()))
    init_task = asyncio.create_task(load_or_init(face, config.state_directory))

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
        await face.save(config.state_directory)

        logger.info("Cleaning up...")
        await face.cleanup()


@cli.command()
def main(
    config_file: Optional[FileText] = typer.Option(
        None, "--config-file", "-C", dir_okay=False, help="Configuration file."
    ),
    config: Optional[List[str]] = typer.Option(
        None, "--config", "-c", help="Configuration entries."
    ),
    verbosity: log.Verbosity = typer.Option(
        "INFO", "--verbosity", "-v", help="Verbosity level."
    ),
) -> None:
    """Command line interface for cilroy."""

    log.configure(verbosity)

    logger.info("Loading config...")
    try:
        config = get_config(config_file, config)
    except ValueError as e:
        logger.error("Failed to parse config!", exc_info=e)
        raise typer.Exit(1)
    logger.info("Config loaded!")

    asyncio.run(run(config))


if __name__ == "__main__":
    # entry point for "python -m"
    cli()