from datetime import datetime

from discord import Embed
from discord.ext import commands


class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name='ping', description='Measure current latency of the bot!')
    async def ping(self, ctx):
        time_received = ctx.message.created_at
        ping_message = await ctx.send(embed=Embed(description='placeholder'))
        return await ping_message.edit(embed=Embed(
            description=f'Pong! **`{int((ping_message.created_at - time_received).total_seconds() * 1000)}ms`**',
            timestamp=datetime.now()))


def setup(bot):
    bot.add_cog(GeneralCommands(bot))
