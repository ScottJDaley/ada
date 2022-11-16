import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from ada.cog import Cog


class Bot(commands.Bot):
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        cmd_prefix = os.getenv("DISCORD_PREFIX")
        if not cmd_prefix:
            cmd_prefix = "ada "
        print(f"Discord Prefix: '{cmd_prefix}'")
        super().__init__(
            command_prefix=commands.when_mentioned_or(cmd_prefix),
            intents=discord.Intents.default()
        )
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
        guilds = None
        if self.guild:
            guilds = [self.guild]
        await self.add_cog(Cog(self), guilds=guilds)
        if self.guild:
            await self.tree.sync(guild=self.guild)
        else:
            await self.tree.sync()
        print("Loaded cogs")

    def run(self):
        super(Bot, self).run(self.token)


bot = Bot()
bot.run()
