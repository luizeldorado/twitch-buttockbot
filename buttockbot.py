import butt
import twitchio
import random
import os
import psycopg2

class ChannelInfo():
	def __init__(self, name, messages_target, messages_probability):
		self.name = name
		self.messages_target = messages_target
		self.messages_probability = messages_probability
		self.messages_current = 0

class ButtockBot(twitchio.Client):
	def __init__(self):

		print('Starting...')

		self.channels = []

		# Get environment variables
		self.database_url = os.environ['DATABASE_URL']
		self.twitch_bot_token = os.environ['TWITCH_BOT_TOKEN']

		# Connect to database
		print('Connecting the database...')
		self.conn = psycopg2.connect(self.database_url)
		self.cur = self.conn.cursor()

		# Connect to IRQ
		print('Connecting to Twitch\'s IRQ...')
		super().__init__(token=self.twitch_bot_token)

	async def event_ready(self):
		print(f'Logged in as {self.nick}')

		await self.join_channels([self.nick])
		print(f'Joined self channel {self.nick}')

		# TODO Check on database to join all already joined channels
		# TODO Check on database to get messages target and probability

		self.channels = []
		# self.channels = [ChannelInfo('luiz_eldorado', 0, 1)]

		await self.join_channels(channel.name for channel in self.channels if channel.name != self.nick)
		print(f'Joined {len(self.channels)} channels')

	async def event_join(self, channel, user):
		print(f'event_join: {channel}, {user}')

	async def event_part(self, user):
		print(f'event_part: {user}')

	async def event_message(self, message):
		if message.echo:
			return

		print(f'{message.channel.name} / {message.author.name}: {message.content}')

		# Do commands inside own chat
		if message.channel.name == self.nick:

			if await self.parse_commands(message):
				return

			# 'Set the probability that a message will not be randomly skipped.'

		# In other chats, just butt
		
		# Find ChannelInfo class
		channel_info = next((x for x in self.channels if x.name == message.channel.name), None)	
		if channel_info == None:
			return

		butted_message = butt.buttify(message.content, do_print=False)

		if self.check_should_butt(channel_info, message.content, butted_message):
			channel_info.messages_current = 0

			await message.channel.send(butted_message)
			print(f'=> {butted_message}')

		else:
			channel_info.messages_current += 1

	async def parse_commands(self, message):
		if not message.content.startswith('!'):
			return False

		args = message.content.split()

		if len(args) >= 1:

			channel_info = next((x for x in self.channels if x.name == message.author.name), None)

			if args[0] == '!help':
				await message.channel.send('Commands: !help !info !joinme !leaveme !setfrequency <0..n> !setprobability <0..1>')

			elif args[0] == '!info':
				if channel_info != None:
					await message.channel.send(f'@{message.author.name} Joined, frequency: {channel_info.messages_target}, probability: {channel_info.messages_probability}')
				else:
					await message.channel.send(f'@{message.author.name} Not joined')

			elif args[0] == '!joinme':

				if channel_info == None:
					self.channels.append(ChannelInfo(message.author.name, 50, 1))
					await self.join_channels([message.author.name])
					await message.channel.send(f'@{message.author.name} I\'ve joined your channel!')

					# TODO Store in database

				else:
					await message.channel.send(f'@{message.author.name} I have already joined your channel.')

			elif args[0] == '!leaveme':

				if channel_info != None:
					self.channels.remove(channel_info)
					self.part_channel(message.author.name)
					await message.channel.send(f'@{message.author.name} I have left your channel.')

					# TODO Store in database

				else:
					await message.channel.send(f'@{message.author.name} I\'m not joined in your channel!')

			elif args[0] == '!setfrequency' and len(args) >= 2:

				if channel_info != None:
					try:
						frequency = int(args[1])
						if frequency < 0:
							raise ValueError()

						channel_info.messages_target = frequency
						# TODO Store in database

						await message.channel.send(f'@{message.author.name}\'s frequency set to {frequency}')

					except ValueError:
						await message.channel.send(f'@{message.author.name} Invalid value!')

				else:
					await message.channel.send(f'@{message.author.name} I am not joined in your channel!')

			elif args[0] == '!setprobability' and len(args) >= 2:
				if channel_info != None:
					try:
						probability = float(args[1])
						if probability < 0 or probability > 1:
							raise ValueError()

						channel_info.messages_probability = probability
						# TODO Store in database

						await message.channel.send(f'@{message.author.name}\'s probability set to {probability}')

					except ValueError:
						await message.channel.send(f'@{message.author.name} Invalid value!')

				else:
					await message.channel.send(f'@{message.author.name} I am not joined in your channel!')

		return True

	def part_channel(self, channel):
		# TODO manually send PART to twitch icq
		pass

	def check_should_butt(self, channel_info, original_message, butted_message):

		if channel_info.messages_current < channel_info.messages_target:
			return False

		if random.random() >= channel_info.messages_probability:
			return False

		if not ((butted_message != original_message) and (butted_message.lower() != 'butt')):
			return False

		return True


if __name__ == '__main__':
	bot = ButtockBot()
	bot.run()