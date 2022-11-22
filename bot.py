import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from ada.ada import Ada
from ada.cog import AdaCog


class Bot(commands.Bot):
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        cmd_prefix = os.getenv("DISCORD_PREFIX")
        if not cmd_prefix:
            cmd_prefix = "ada "
        print(f"Discord Prefix: '{cmd_prefix}'")
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned_or(cmd_prefix),
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
        guilds = None
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
bot.run()
