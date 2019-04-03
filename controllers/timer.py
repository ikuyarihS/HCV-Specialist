import json
import math
from datetime import datetime

from discord import Embed
from discord.ext import commands


class Timer(commands.Cog):
    """[summary]
    """

    example = 'For example: !timer 19/4/10 14:00 Remind me!'
    create_timer_desc = f'Create a timer / checkmark and countdown toward it!\n{example}'
    checkmarks: dict = {}
    client = None

    def __init__(self, bot):
        """Initiate a new Timer

        Arguments:
            bot {commands.Bot} -- current Bot
        """

        self.bot: commands.Bot = bot
        Timer.client = bot
        self.initiated = False

        self.initiate()

        # print(Timer.checkmarks)

    def initiate(self):
        try:
            with open('data/timer.json') as data:
                Timer.checkmarks = json.load(data)

            for checkmark in self.checkmarks.values():
                checkmark['date'] = datetime.strptime(checkmark['date'], '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(e)

    def store_data(self):
        def myconverter(o):
            if isinstance(o, datetime):
                return o.__str__()

        try:
            with open('data/timer.json', 'w') as data:
                json.dump(Timer.checkmarks, data, indent=4, default=myconverter)
        except RuntimeError:
            pass

    @staticmethod
    async def check_time():
        for key, checkmark in Timer.checkmarks.items():
            channel = Timer.client.get_guild(552997494641000468).get_channel(checkmark['channel_id'])
            if not channel:
                del Timer.checkmarks[key]
                continue

            await channel.edit(name=f"{checkmark['desc']}: {Timer.get_timer(checkmark['date'])}")

    @staticmethod
    def get_timer(date) -> str:
        """A "simple" function to get abyss timer.

        Returns:
            str -- Current abyss timer.
        """
        diff_time = date - datetime.now()

        if diff_time.total_seconds() < 0:
            return 'overdue!'

        diff_ms = diff_time.total_seconds() * 1000
        diff_days = diff_time.days  # math.floor(diff_ms / 86400000)
        diff_hours = math.floor((diff_ms % 86400000) / 3600000)
        diff_minutes = math.floor(((diff_ms % 86400000) % 3600000) / 60000)

        current_time = "{day}{hour}{min}".format(
            day=Timer.no_zero(diff_days, "d "),
            hour="0{h}h".format(h=diff_hours)[-3:]
            if diff_days > 0 else Timer.no_zero(diff_hours, "h"),
            min="0{m}m".format(m=diff_minutes)[-3:]
            if (diff_days > 0 or diff_hours) and diff_minutes > 0
            else Timer.no_zero(diff_minutes, 'm'))

        return current_time

    @staticmethod
    def no_zero(number, text_if_not_zero):
        return "{}{}".format(number, text_if_not_zero) if number != 0 else ""

    @commands.command(pass_context=True, name='timer', description=create_timer_desc)
    async def create_timer(self, ctx, *args):
        try:
            date = await Timer.datetime_from(ctx, args[0], args[1])
            desc = ' '.join(args[2:])

            channel = await ctx.guild.create_voice_channel(name='Placeholder',
                                                           category=self.bot.get_channel(562854126418001920))

            Timer.checkmarks[str(ctx.message.id)] = {
                'date': date,
                'desc': desc,
                'channel_id': channel.id
            }

            self.store_data()

            await ctx.send(embed=Embed(description=f'Received date {date}, description: {desc}'))
            await Timer.check_time()
        except IndexError:
            return await Timer.quit_with_message(ctx, f'Wrong date format.\nCorrect example: `!{Timer.example}``')

    @staticmethod
    async def quit_with_message(ctx, quit_message):
        await ctx.send(embed=Embed(description=quit_message))
        return None

    @staticmethod
    async def datetime_from(ctx, date_str, hour_str):
        try:
            date_stuff = [int(x) for x in date_str.split('/')]
            if date_stuff[0] < 1000:
                date_stuff[0] += 2000

            hour_stuff = [int(x) for x in hour_str.split(':')]

            if len(date_stuff) != 3 or len(hour_stuff) != 2:
                return await Timer.quit_with_message(ctx, f'Wrong date format.\nCorrect example: `!{Timer.example}')

            date = datetime(*date_stuff, *hour_stuff)

            return date

        except ValueError:
            return await Timer.quit_with_message(ctx, f'Wrong date format.\nCorrect example: `!{Timer.example}')


def setup(bot):
    bot.add_cog(Timer(bot))


check_time = Timer.check_time
