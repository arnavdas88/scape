class CommandError(Exception):
    pass

class DependencyError(CommandError):
    pass

class ExecutionError(CommandError):
    pass

class SerializationError(CommandError):
    pass
