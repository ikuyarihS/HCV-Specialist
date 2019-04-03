import gc
import math
import os
import time
import traceback
from datetime import datetime
import asyncio

import schedule
from discord import Embed, Forbidden, Game
from discord.ext import commands
from controllers.timer import check_time

client = commands.Bot(command_prefix=os.environ['prefix'])

STARTUP_EXTENSIONS: list = [
    'controllers.general_commands',
    'controllers.timer'
]

log_channel = None
timer = time.time()


async def send_log(ctx, title: str, color: int, description: str, footer: str = ''):
    global log_channel

    if not log_channel:
        log_channel = client.get_channel(500552823390601216)

    log_embed = Embed(title=title, color=color, description=description, timestamp=datetime.now())

    for name, value in (('Channel', f'<#{ctx.channel.id}>'),
                        ('User', f'<@{ctx.author.id}>'),
                        ('Command', ctx.command),
                        ('Content', ctx.message.content[:2048])):
        log_embed.add_field(name=name, value=value)

    log_embed.set_thumbnail(url=ctx.message.author.avatar_url)

    if footer:
        log_embed.set_footer(text=footer)

    return await log_channel.send(embed=log_embed)


async def timer_job():
    while not client.is_closed():
        await check_time()
        await asyncio.sleep(30)


@client.event
async def on_ready():
    """When the client is ready. Most of the time it's name change and activity set and stuff."""
    global log_channel

    if not log_channel:
        log_channel = client.get_channel(562863510477078540)

    schedule.every().minute.do(clean_up_job)

    await client.wait_until_ready()
    await client.change_presence(activity=Game("Reading Zine"))

    # client.loop.create_task(remind_job())
    client.loop.create_task(timer_job())

    return await log_channel.send(embed=create_status_report())


def create_status_report() -> Embed:
    print(f"Logged in as {client.user.name}")
    print(f'{client.user.name} is ready!')

    status_report = Embed(color=0x1A5276, title='Status report', timestamp=datetime.now()) \
        .set_thumbnail(url=client.user.avatar_url) \
        .add_field(name='Logged in as:', value=client.user.name) \
        .add_field(name='Extension status:', value="\n".join(extension_status)) \
        .add_field(name='Current servers:', value='\n'.join(f'• {x.name}' for x in client.guilds)) \
        .set_footer(text=f'Took {round(time.time() - timer, 2)}s')

    return status_report


@client.event
async def on_command_error(ctx, error):
    """Welp, stuff happens.

    Arguments:
        ctx {[commands.Context]} -- [description]
        error {[]} -- [description]
    """

    # if command has local error handler, return
    if not ctx.command:
        return
        # Old code > return await send_log(ctx, 'Unknown command', 0xE74C3C, 'Unregistered command.')
        # Old code > return await log_channel.send(f'Unregistered command: {ctx.message.content}')

    await ctx.message.add_reaction('❌')

    if hasattr(ctx.command, 'on_error'):
        return

    # get the original exception
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.BotMissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'I need the **{}** permission(s) to run this command.'.format(fmt)
        await ctx.send(_message)
        return

    if isinstance(error, commands.DisabledCommand):
        await ctx.send('This command has been disabled.')
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please retry in {}s.".format(math.ceil(error.retry_after)))
        return

    if isinstance(error, commands.MissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
        await ctx.send(_message)
        return

    if isinstance(error, commands.UserInputError):
        await ctx.send("Invalid input.")
        return

    if isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send('This command cannot be used in direct messages.')
        except Forbidden:
            pass
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")
        return

    # ignore all other exception types, but print them to stderr
    error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    if len(error_traceback) > 2000:
        return print(error_traceback)

    return await send_log(ctx, 'Unhandled exception prevented', 0xff0000, f'```py\n{error_traceback}```')


@client.before_invoke
async def client_before_invoke(ctx):
    global timer
    timer = time.time()


@client.after_invoke
async def client_after_invoke(ctx):
    # Nope, still handling it
    if ctx.invoked_subcommand:
        return

    return await send_log(ctx=ctx, title='Command invoked', color=0x1A5276,
                          description='A command was successfully invoked.',
                          footer=f'Took {round(time.time() - timer, 2)}s • ID: {ctx.author.id}')


def clean_up_job():
    gc.collect()


if __name__ == "__main__":
    extension_status = []
    for extension in STARTUP_EXTENSIONS:
        try:
            client.load_extension(extension)
            status = f'• \\✅ Loaded extension {extension}'
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            status = f'• \\❌ Failed to load extension `{extension}`\n```py\n{exc}```'

        extension_status.append(status)
        print(status)

    client.run(os.environ['token'])
