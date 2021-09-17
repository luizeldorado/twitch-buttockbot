import butt

import psycopg2
import twitchio

from pprint import pprint
import random
import os

class ChannelInfo():
	def __init__(self, twitch_name, activated, frequency, probability):
		self.twitch_name = twitch_name
		self.activated = activated
		self.frequency = frequency
		self.probability = probability
		self.messages_current = 0

	def __repr__(self):
		return f"ChannelInfo({self.twitch_name}, act={self.activated}, freq={self.frequency}, prob={self.probability}, cur={self.messages_current})"

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

		# Get info on channels from database
		self.cur.execute("SELECT twitch_name, activated, frequency, probability from channels;")
		result = self.cur.fetchall()

		pprint(result)

		self.channels = []

		for twitch_name, activated, frequency, probability in result:
			channel_info = ChannelInfo(twitch_name, activated, frequency, probability)
			self.channels.append(channel_info)
			print(channel_info)

		channel_names = [channel.twitch_name for channel in self.channels if channel.activated and channel.twitch_name != self.nick]

		pprint(channel_names)

		await self.join_channels(channel_names)

		print(f'Joined {len(channel_names)}/{len(self.channels)} channels')

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

		# In other chats, just butt
		
		# Find ChannelInfo class of channel where message was sent to
		channel_info = self.get_channel_info(message.channel.name)
		if channel_info == None or channel_info.activated != True:
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

			# Find ChannelInfo class of user that sent the message
			channel_info = self.get_channel_info(message.author.name)

			if args[0] == '!help':
				await message.channel.send(f'@{message.author.name} Commands: !help !joinme !leaveme !info !deleteinfo !setfrequency <0..n> !setprobability <0..1>')

			elif args[0] == '!joinme':

				if channel_info != None and channel_info.activated == True:
					await message.channel.send(f'@{message.author.name} I have already joined your channel.')

				else:

					if channel_info == None:
						channel_info = self.insert_channel(message.author.name, activated=True)
					else:
						channel_info.activated = True

						self.cur.execute("UPDATE channels SET activated=TRUE WHERE twitch_name=%s;", (message.author.name,))
						self.conn.commit()

					await self.join_channels([message.author.name])
					await message.channel.send(f'@{message.author.name} I\'ve joined your channel!')

			elif args[0] == '!leaveme':

				if channel_info == None or channel_info.activated == False:
					# No need to add new ChannelInfo
					await message.channel.send(f'@{message.author.name} I\'m not joined in your channel!')

				else:
					channel_info.activated = False

					self.cur.execute("UPDATE channels SET activated=FALSE WHERE twitch_name=%s;", (message.author.name,))
					self.conn.commit()

					self.part_channel(message.author.name)
					await message.channel.send(f'@{message.author.name} I have left your channel.')

			elif args[0] == '!info':

				if channel_info != None:
					await message.channel.send(f'@{message.author.name} {"Joined" if channel_info.activated else "Not joined"}, frequency: {channel_info.frequency}, probability: {channel_info.probability}')
				else:
					await message.channel.send(f'@{message.author.name} Not joined, no other information')

			elif args[0] == '!deleteinfo':

				if channel_info == None:
					await message.channel.send(f'@{message.author.name} There\'s no information to delete.')
				else:
					
					if channel_info.activated:
						await message.channel.send(f'@{message.author.name} I am current joined in your channel, please !leaveme before deleting your information.')
					
					else:
						self.channels.remove(channel_info)

						self.cur.execute("DELETE FROM channels WHERE twitch_name=%s;", (message.author.name,))
						self.conn.commit()

						await message.channel.send(f'@{message.author.name} Your information was deleted.')

			elif args[0] == '!setfrequency' and len(args) >= 2:
				
				try:
					frequency = int(args[1])
					if frequency < 0:
						raise ValueError()

					if channel_info == None:
						# Add channel with activated as false
						channel_info = self.insert_channel(message.author.name, activated=False, frequency=frequency)

					else:
						channel_info.frequency = frequency
						self.cur.execute("UPDATE channels SET frequency=%s WHERE twitch_name=%s;", (frequency, message.author.name,))
						self.conn.commit()

					await message.channel.send(f'@{message.author.name}\'s frequency set to {frequency}')

				except ValueError:
					await message.channel.send(f'@{message.author.name} Invalid value!')

			elif args[0] == '!setprobability' and len(args) >= 2:

				try:
					probability = float(args[1])
					if probability < 0 or probability > 1:
						raise ValueError()

					if channel_info == None:
						# Add channel with activated as false
						channel_info = self.insert_channel(message.author.name, activated=False, probability=probability)

					else:
						channel_info.probability = probability
						self.cur.execute("UPDATE channels SET probability=%s WHERE twitch_name=%s;", (probability, message.author.name,))
						self.conn.commit()

					await message.channel.send(f'@{message.author.name}\'s probability set to {probability}')

				except ValueError:
					await message.channel.send(f'@{message.author.name} Invalid value!')

			pprint(channel_info)

		return True

	def get_channel_info(self, channel_name):
		return next((channel for channel in self.channels if channel.twitch_name == channel_name), None)

	def insert_channel(self, twitch_name, activated, frequency=50, probability=1):
		channel_info = ChannelInfo(twitch_name, activated, frequency, probability)
		self.channels.append(channel_info)

		self.cur.execute("INSERT INTO channels (twitch_name, activated, frequency, probability) VALUES (%s, %s, %s, %s);",
			(twitch_name, activated, frequency, probability,))
		self.conn.commit()

		return channel_info

	def part_channel(self, channel):
		# TODO manually send PART to twitch icq
		pass

	def check_should_butt(self, channel_info, original_message, butted_message):

		if channel_info.messages_current < channel_info.frequency:
			return False

		if random.random() >= channel_info.probability:
			return False

		if not ((butted_message != original_message) and (butted_message.lower() != 'butt')):
			return False

		return True


if __name__ == '__main__':
	bot = ButtockBot()
	bot.run()