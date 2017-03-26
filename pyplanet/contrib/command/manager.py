from pyplanet.apps.core.maniaplanet.callbacks import player
from pyplanet.core.events import receiver
from pyplanet.contrib.command.command import Command
from pyplanet.core import signals
from pyplanet.core.instance import Controller


class _CommandManager:
	def __init__(self):
		self.commands = list()

		self.on_start()
		self.on_chat()

	@receiver(signals.pyplanet_start_after)
	async def on_start(self, **kwargs):
		tst_cmd = Command(command='ok', target=self.target)
		tst_cmd.add_param('times', type=int)

		self.commands.extend([
			tst_cmd
		])
		pass

	async def target(self, player, data, **kwargs):
		await Controller.instance.gbx.execute(
			'ChatSendServerMessageToLogin',
			'$z$s >> You just did /ok. Parameters we got: {}'.format(str(data)),
			player.login
		)
		print(player, data, kwargs)

	@receiver(player.player_chat)
	async def on_chat(self, player, text, cmd, **kwargs):
		# Only take action if the chat entry is a command.
		if not cmd:
			return

		# Parse command.
		argv = text.split(' ')
		if not argv:
			return

		# Replace the / in the first part.
		argv[0] = argv[0][1:]

		# Try to match the command prefix by one of the registered commands.
		command = None
		for cmd in self.commands:
			if cmd.match(argv):
				command = cmd
				break

		# Let the command handle the logic it needs.
		if command:
			await command.handle(player, argv)


CommandManager = _CommandManager()
