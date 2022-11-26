import os
from typing import Literal, Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

from ada.ada import Ada
from ada.cog import AdaCog


class Bot(commands.Bot):
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
        )
        self.sync = os.getenv('SYNC_COMMANDS', 'false').lower() == 'true'
        self.guild = None
        restrict_slash_commands_to_guild = os.getenv("RESTRICT_SLASH_COMMANDS_TO_GUILD")
        print(restrict_slash_commands_to_guild)
        if restrict_slash_commands_to_guild:
            self.guild = discord.Object(id=restrict_slash_commands_to_guild)
            print(
                f'Restricting slash commands to guild_id "{restrict_slash_commands_to_guild}"'
            )
        else:
            print(
                "Setting up global slash commands.\n"
                "NOTE: For this to work, all servers with the bot must have the applications.commands scope."
            )

    async def setup_hook(self):
        print(f"Logged in as {self.user}")
        guilds = discord.utils.MISSING
        if self.guild:
            guilds = [self.guild]
        await self.add_cog(AdaCog(self, Ada()), guilds=guilds)
        if self.sync:
            if self.guild:
                print(f"Syncing commands to guild {self.guild}")
                await self.tree.sync(guild=self.guild)
            else:
                print(f"Syncing commands globally")
                await self.tree.sync()
        print("Loaded cogs")

    def run(self, **kwargs):
        super(Bot, self).run(self.token)


bot = Bot()


# @bot sync -> global sync
# @bot sync ~ -> sync current guild
# @bot sync * -> copies all global app commands to current guild and syncs
# @bot sync ^ -> clears all commands from the current guild target and syncs (removes guild commands)
# @bot sync id_1 id_2 -> syncs guilds with id 1 and 2
@bot.command("sync")
@commands.guild_only()
@commands.is_owner()
async def sync(
        ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None
) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


bot.run()
