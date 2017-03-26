import re
from inspect import iscoroutinefunction

from pyplanet.contrib.command.params import ParameterParser
from pyplanet.core.instance import Controller


class Command:
	"""
	The command instance describes the command itself, the target to fire and all other related information, like
	admin command or aliases.
	"""

	def __init__(
		self, command, target, aliases=None, admin=False, namespace=None, parser=None
	):
		"""
		Initiate a command.
		:param command: Command text (prefix without parameters).
		:param target: Target method to fire.
		:param aliases: Alias(ses) for the command.
		:param admin: Register command in admin context.
		:param namespace: Custom namespace, this can be used to create commands like '/prog start' and '/prog end' 
						  where 'prog' is the namespace.
		:param parser: Custom parser.
		:type command: str
		:type target: any
		:type aliases: str[]
		:type admin: bool
		:type namespace: str
		:type parser: any
		"""
		self.command = command
		self.target = target
		self.aliases = aliases or list()
		self.admin = admin
		self.namespace = namespace
		self.parser = parser or \
					  ParameterParser('{} {}'.format(self.namespace, self.command) if self.namespace else self.command)
		self.__regex = None

	def match(self, raw):
		"""
		Try to match the command with the given input in array style (splitted by spaces).
		:param raw: Raw input, split by spaces.
		:type raw: list
		:return: Boolean if command matches.
		"""
		input = raw[:]
		if self.namespace and input[0] == self.namespace:
			input.pop(0)
		elif self.namespace:
			return False
		if not len(input):
			return False

		command = input.pop(0)
		if self.command == command or command in self.aliases:
			return True
		return False

	def get_params(self, input):
		"""
		Get params in array from input in array.
		:param input: Array of raw input.
		:type input: list
		:return: Array of parameters, stripped of the command name and namespace, if defined.
		:rtype: list
		"""
		if self.namespace:
			input.pop(0)
		input.pop(0)
		return input

	def add_param(
		self, name: str,
		nargs=1,
		type=str,
		default=None,
		required: bool=True,
		help: str=None,
		dest: str=None,
	):
		"""
		Add positional parameter.
		:param name: Name of parameter, will be used to store result into!
		:param nargs: Number of arguments, use integer or '*' for multiple or infinite.
		:param type: Type of value, keep str to match all types. Use any other to try to parse to the type.
		:param default: Default value when no value is given.
		:param required: Set the parameter required state, defaults to true.
		:param help: Help text to display when parameter is invalid or not given and required.
		:param dest: Destination to save into namespace result (defaults to name).
		:return: parser instance
		:rtype: pyplanet.contrib.command.command.Command
		"""
		self.parser.add_param(
			name=name, nargs=nargs, type=type, default=default, required=required, help=help, dest=dest
		)
		return self

	async def handle(self, player, argv):
		"""
		Handle command parsing and execution.
		:param player: Player object.
		:param argv: Arguments in array
		:type player: pyplanet.apps.core.maniaplanet.models.player.Player
		"""
		# Strip off the namespace and command.
		paramv = self.get_params(argv)

		# Parse, validate and show errors if any.
		self.parser.parse(paramv)
		if not self.parser.is_valid():
			await Controller.instance.gbx.execute(
				'ChatSendServerMessageToLogin',
				'$z$s >> Command operation got invalid arguments: {}'.format(', '.join(self.parser.errors)),
				player.login
			)
			return

		# We are through. Call our target!
		if iscoroutinefunction(self.target):
			return await self.target(player=player, data=self.parser.data, raw=argv)
		return self.target(player=player, data=self.parser.data, raw=argv)

	def __str__(self):
		return 'Command: /{} {}'.format(self.namespace or self.command, self.command if self.namespace else '')