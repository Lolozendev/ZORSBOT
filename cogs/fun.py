import discord
from discord.ext import commands
from main import ZORS
from utils.zors_cog import ZorsCog


class Fun(ZorsCog):
    def __init__(self, bot: ZORS):
        self.bot = bot

    @commands.slash_command(name="ping", description="Check if the bot is alive.")
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Pong! thanks for checking on me {ctx.author.mention} !")


def setup(bot: ZORS):
    bot.add_cog(Fun(bot))
