import traceback


import discord
from discord import Guild
from discord.ext import commands
from typing_extensions import override

from utils import logger
from loguru import logger as log
from asyncio import run
from utils.settings import settings
from model.database import Database


class ZORS(commands.Bot):
    database: Database

    def __init__(self, *args, **kwargs):
        log.debug("ZORS bot is starting up...")
        super().__init__(*args, **kwargs)
        self.database = Database(str(settings.postgres_url))
        log.info("Successfully connected to the database")
        log.trace("ZORS bot has been initialized.")
        log.info("Loading cogs...")

    @classmethod
    async def create_bot(cls) -> "ZORS":
        """
        Creates an instance of the bot.
        Returns: ZORS - Instance of the bot.
        """
        zorsintents = discord.Intents.none()
        zorsintents.members = True
        zorsintents.guilds = True
        zorsintents.guild_messages = True
        zorsintents.bans = True
        zorsintents.emojis_and_stickers = True
        zorsintents.webhooks = True
        zorsintents.messages = True
        zorsintents.message_content = True
        zorsintents.reactions = True
        zorsintents.auto_moderation_configuration = True
        zorsintents.auto_moderation_execution = True
        zorsintents.voice_states = True

        bot = ZORS(
            description="ZORS !",
            activity=discord.Activity(type=discord.ActivityType.custom, name="ZORS !"),
            intents=zorsintents,
            help_command=None,
        )
        await bot.database.create_db_and_tables()
        bot._load_cogs()
        return bot

    @property
    def main_guild(self) -> Guild:
        guild = self.get_guild(settings.main_guild)
        if guild is None:
            log.error("Main guild not found.")
            raise ValueError("Main guild not found.")
        return guild

    @override
    async def start(self, *args, **kwargs) -> None:
        """
        Starts the bot with the token from the settings.
        Returns:

        """
        await super().start(settings.discord_token, *args, **kwargs)

    def _load_cogs(self) -> None:
        """
        Loads all cogs in the cogs directory recursively.
        python files starting with an underscore aren't started. This is default pycord behavior.

        Returns:

        """
        status = self.load_extensions("cogs", recursive=True, store=True)
        if status is None:
            log.debug("No cogs loaded.")
            return
        for extension in status:
            match status[extension]:
                case True:
                    log.debug(f"Loaded cog: {extension}")
                case discord.ExtensionAlreadyLoaded:
                    log.debug(f"Cog already loaded: {extension} - {status[extension]}")
                case discord.ExtensionNotFound:
                    log.error(f"Failed to load cog: {extension} - {status[extension]}")
                case discord.NoEntryPointError:
                    log.error(
                        f"Cog has no setup function: {extension} - {status[extension]}"
                    )
                case discord.ExtensionFailed:
                    log.error(f"Cog failed to load: {extension} - {status[extension]}")
                case _:
                    log.error(f"Unknown error: {extension} - {status[extension]}")
                    print(traceback.format_exc())


@log.catch(
    level="CRITICAL",
    message="Unexpected error occurred, that forced the bot to shut down.",
)
async def main():
    logger.setup_logger()
    zors_bot = await ZORS.create_bot()
    await zors_bot.start()


if __name__ == "__main__":
    run(main())
