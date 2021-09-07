import butt
from twitchio.ext import commands
import random
import os

class Bot(commands.Bot):

	def __init__(self):

		print('Init')

		self.messages_target = int(os.environ['TWITCH_BOT_MESSAGE_TARGET'])
		self.messages_current = 0

		self.messages_probability = float(os.environ['TWITCH_BOT_MESSAGE_PROBABILITY'])

		super().__init__(token=os.environ['TWITCH_BOT_TOKEN'], prefix='?', initial_channels=[os.environ['TWITCH_BOT_CHANNEL']])
		print('Connected')

	async def event_ready(self):
		print(f'Logged in as {self.nick}')

	async def event_message(self, message):
		if message.echo:
			return

		print('MSG: ' + str(message.author) + ': ' + str(message.content))

		if self.messages_current >= self.messages_target:

			butted_message = butt.buttify(message.content, do_print=False)

			if (butted_message != message.content) and (butted_message.lower() != 'butt'):

				r = random.random()
				if r < self.messages_probability:
					self.messages_current = 0

					ctx = await self.get_context(message)
					await ctx.send(butted_message)

					print('===>', butted_message)

		else:
			self.messages_current += 1

bot = Bot()
bot.run()