
import discord
from discord import Member, Guild, User, RoleTags, Role
from discord.ext import commands

from main import ZORS
from model.managers import HabitueManager
from loguru import logger as log



class Habitue(commands.Cog):
    rolename = "Les Habitués"
    category_role = "==COULEURS HABITUÉS=="
    habitue_colorname_template = "couleur {username}"

    default_colors = {
        "blue": discord.Color.blue(),
        "blurple": discord.Color.blurple(),
        "fuchsia": discord.Color.fuchsia(),
        "gold": discord.Color.gold(),
        "green": discord.Color.green(),
        "greyple": discord.Color.greyple(),
        "magenta": discord.Color.magenta(),
        "og_blurple": discord.Color.blurple(),
        "orange": discord.Color.orange(),
        "purple": discord.Color.purple(),
        "red": discord.Color.red(),
        "teal": discord.Color.teal(),
        "yellow": discord.Color.yellow(),
    }

    default_colors_list = [el for el in default_colors.keys()]

    def __init__(self, bot:ZORS):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if self.rolename not in str(before.roles) and self.rolename in str(after.roles):
            log.info(f"{after.display_name} was given the habitue role")
            await self._add_habitue(after.guild, after)
        elif self.rolename in str(before.roles) and self.rolename not in str(after.roles):
            log.info(f"{after.display_name} was removed from the habitue role")
            await self._remove_habitue(after.guild, after)

    @commands.slash_command(name="add_habitue", description="Add a habitue to the server.")
    @commands.has_permissions(manage_roles=True)
    @discord.option(name="member", description="The member you want to add.", type=discord.Member, required=True)
    @discord.option(name="color", description="The color you want to set as a hex code (#XXYYZZ).", type=str, required=False)
    async def add_habitue_command(self, ctx: discord.ApplicationContext, member: Member, color: str | None = None):
        if self.rolename in str(member.roles):
            log.error(f"{member.display_name} is already an habitue")
            await ctx.respond(f"{member.display_name} is already an habitue")
        else:
            await self._add_habitue(ctx.guild, member, color)
            await ctx.respond(f"{member.display_name} has been added has an habitue.")

    @commands.slash_command(name="remove_habitue", description="Remove a habitue from the server.")
    @commands.has_permissions(manage_roles=True)
    @discord.option(name="member", description="The member you want to remove.", type=discord.Member, required=True)
    async def remove_habitue_command(self, ctx: discord.ApplicationContext, member: Member):
        if self.rolename not in str(member.roles):
            log.error(f"{member.display_name} is not an habitue")
            await ctx.respond(f"{member.display_name} is not an habitue")
        else:
            await self._remove_habitue(ctx.guild, member)
            await ctx.respond(f"{member.display_name} has been removed as an habitue.")

    @commands.slash_command(name="set_custom_color", description="Set your color.")
    @commands.has_role(rolename)
    @discord.option(
        name="red",
        description="The amount of red you want to set.",
        type=int,
        required=True,
        min_value=0,
        max_value=255,
    )
    @discord.option(
        name="green",
        description="The amount of green you want to set.",
        type=int,
        required=True,
        min_value=0,
        max_value=255,
    )
    @discord.option(
        name="blue",
        description="The amount of blue you want to set.",
        type=int,
        required=True,
        min_value=0,
        max_value=255,
    )
    async def set_custom_color(self, ctx: discord.ApplicationContext, red: int, green: int, blue: int):
        color_name = await self._update_user_color(ctx.user, red, green, blue)
        await ctx.respond(f"Your color has been set to {color_name}.")

    @commands.slash_command(
        name="set_color", description="Set your color from a list of predefined colors."
    )
    @commands.has_role(rolename)
    @discord.option(
        name="color",
        description="The color you want to set.",
        type=str,
        required=True,
        choices=default_colors_list,
    )
    async def set_color(self, ctx: discord.ApplicationContext, color: str):
        r, g, b = self.default_colors[color].to_rgb()
        await self._update_user_color(ctx.user, r, g, b)
        await ctx.respond(f"Your color has been set to {color}.")

    #region utility functions
    async def _update_user_color(self, member: User|Member,red:int, green:int, blue:int) -> str:
        role = discord.utils.get(member.guild.roles, name=self.habitue_colorname_template.format(username=member.display_name))
        if role is None:
            log.warning(f"Role {self.habitue_colorname_template.format(username=member.display_name)} not found in the guild {member.guild.name}")
            if self.rolename in str(member.roles):
                log.warning(f"{member.display_name} seems to be an habitue, creating the color role")
                role = await self._create_color_role(member.guild, member.display_name)
                await member.add_roles(role)
        await role.edit(color=discord.Color.from_rgb(red, green, blue))
        async with self.bot.database.get_session() as session:
            await HabitueManager.update_color(session, member, f"#{red:02x}{green:02x}{blue:02x}")
            await session.commit()
            await session.refresh(await HabitueManager.get_habitue_from_database(session, member))
            color_name = await HabitueManager.get_color_name(session, member)
            return color_name


    async def _add_habitue(self, guild: Guild, member: Member, color: str | None = None):
        habitue_role :RoleTags|None = discord.utils.get(guild.roles, name=self.rolename)
        if habitue_role is None:
            log.error(f"Role {self.rolename} not found in the guild {guild.name}")
            return
        color_role = await self._create_color_role(guild, member.display_name)
        await member.add_roles(habitue_role, color_role)
        async with self.bot.database.get_session() as session:
            await HabitueManager.add(session, member, color)

        log.info(f"Added habitue {member.display_name} to {guild.name}")

    async def _remove_habitue(self, guild: Guild, member: Member):
        habitue_role :RoleTags|None = discord.utils.get(guild.roles, name=self.rolename)
        if habitue_role is None:
            log.error(f"Role {self.rolename} not found in the guild {guild.name}")
            return
        color_role = discord.utils.get(guild.roles, name=self.habitue_colorname_template.format(username=member.display_name))
        await color_role.delete()
        await member.remove_roles(habitue_role)
        async with self.bot.database.get_session() as session:
            await HabitueManager.delete(session, member)
        log.info(f"Removed habitue {member.display_name} from {guild.name}")

    async def _create_color_role(self ,guild: Guild, member_display_name: str) -> Role | None:
        category_position = discord.utils.get(guild.roles, name=self.category_role).position
        if not discord.utils.get(guild.roles, name=self.habitue_colorname_template.format(username=member_display_name)):
            # if the role doesn't exist, create it and set its color to black
            role = await guild.create_role(name=self.habitue_colorname_template.format(username=member_display_name), color=discord.Color.from_rgb(0,0,0))
            await role.edit(position=category_position)
        log.debug(f"Created the color role for {member_display_name}")
        return discord.utils.get(guild.roles, name=self.habitue_colorname_template.format(username=member_display_name))
    #endregion

def setup(bot: ZORS):
    bot.add_cog(Habitue(bot))
