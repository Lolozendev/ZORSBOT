import discord
from discord.ext import commands
from utils import logger, utilities
from utils.database import Database
from loguru import logger as log

class ZORS(commands.Bot):

    def __init__(self, env_vars=None, *args, **kwargs):
        log.debug("ZORS bot is starting up...")
        super().__init__(*args, **kwargs)
        self.logger = log
        self.envs = env_vars
        log.trace("ZORS bot has been initialized.")
        log.debug("Loading cogs...")
        self._load_cogs()

    async def on_ready(self):
        """
        Event that is called when the bot is ready.
        Returns:

        """
        log.debug("ZORS bot is up and ready.")
        log.trace(f"Logged in as {self.user} ({self.user.id})")

    def _load_cogs(self) -> None:
        """
        Loads all cogs in the cogs directory recursively.
        python files starting with an underscore aren't started. This is default pycord behavior.

        Returns:

        """
        status = self.load_extensions("cogs", recursive=True, store=True)
        for extension in status:
            match status[extension]:
                case True:
                    log.debug(f"Loaded cog: {extension}")
                case discord.ExtensionAlreadyLoaded:
                    log.debug(f"Cog already loaded: {extension} - {status[extension]}")
                case discord.ExtensionNotFound:
                    log.error(f"Failed to load cog: {extension} - {status[extension]}")
                case discord.NoEntryPointError:
                    log.error(f"Cog has no setup function: {extension} - {status[extension]}")
                case discord.ExtensionFailed:
                    log.error(f"Cog failed to load: {extension} - {status[extension]}")
                case _:
                    log.error(f"Unknown error: {extension} - {status[extension]}")

@log.catch(level="CRITICAL", message="Unexpected error occurred, that forced the bot to shut down.")
def main() -> None:

    try:
        env_vars = utilities.get_required_env_vars()
        logger.setup_logger('logs' if not "LOGS_PATH" in env_vars else env_vars["LOGS_PATH"], "DEBUG")
    except EnvironmentError as e:
        log.critical(f"Failed to start the bot: {e}")
        exit(1)

    log.debug("Connecting to the database...")
    Database().connect()

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

    zors = ZORS(
        description="ZORS !",
        activity=discord.Game(name="/ping for now"),
        intents=zorsintents,
        help_command=None
    )
    zors.run(env_vars["DISCORD_TOKEN"])

if __name__ == "__main__":
    main()
