
class SSHException(Exception):
  def __enter__(self, ):
    pass
  def __exit__(self, *args, **kwargs):
    pass


class NotConnected(SSHException):
  ...

class UnableToOpenTransport(SSHException):
  ...