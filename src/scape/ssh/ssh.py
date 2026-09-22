import os
import warnings
from socket import socket
from typing import Iterable, Mapping, Optional, TypeAlias

import paramiko
from paramiko.auth_strategy import AuthStrategy
from paramiko.channel import Channel, ChannelFile, ChannelStderrFile, ChannelStdinFile
from paramiko.hostkeys import HostKeys
from paramiko.pkey import PKey
from paramiko.sftp_client import SFTPClient
from paramiko.proxy import ProxyCommand
from paramiko.transport import Transport

from .exceptions import SSHException, NotConnected, UnableToOpenTransport

_Addr: TypeAlias = tuple[str, int]
_SocketLike: TypeAlias = str | _Addr | socket | Channel | ProxyCommand

class SSH:
  def __init__(self,  
        hostname: str,
        port: int = 22,
        username: str | None = None,
        password: str | None = None,
        pkey: PKey | None = None,
        key_filename: str | None = None,
        timeout: float | None = None,
        allow_agent: bool = True,
        look_for_keys: bool = True,
        compress: bool = False,
        sock: _SocketLike | None = None,
        banner_timeout: float | None = None,
        auth_timeout: float | None = None,
        channel_timeout: float | None = None,
        passphrase: str | None = None,
        disabled_algorithms: Mapping[str, Iterable[str]] | None = None,
        transport_factory: Transport | None = None,
        auth_strategy: AuthStrategy | None = None,
    ):
    self.hostname = hostname
    self.port = port

    self.username = username
    self.password = password

    self.pkey = pkey
    self.key_filename = key_filename
    self.passphrase = passphrase

    self.look_for_keys = look_for_keys

    self.sock = sock
    self.timeout = timeout

    self.conn: Optional[paramiko.SSHClient] = None
    self.target = None

    self.connect()

  @property
  def transport(self, ) -> Transport:
    if not self.conn:
      raise NotConnected()

    transport : Optional[Transport] = self.conn.get_transport()
      
    # Check if connection is online
    if transport and not transport.is_active():
        warnings.warn(f"Reconnecting to the jumbpox.")
        self.connect()
        transport : Optional[Transport] = self.conn.get_transport()

    if not transport:
      raise UnableToOpenTransport("Unable to open transport for SSH")

    return transport

  def connect(self, ):
    self.conn = paramiko.SSHClient()
    self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    self.conn.connect(
      self.hostname, self.port, 
      username=self.username, password=self.password,
      pkey=self.pkey, key_filename=self.key_filename, passphrase=self.passphrase,
      look_for_keys=self.look_for_keys,
      timeout=self.timeout, sock=self.sock
    )

    stdin, stdout, stderr = self.conn.exec_command("whoami")
    assert stdout.readlines() == [ f"{self.username}\n" ]

  def disconnect(self, ):
    if self.conn:
        self.conn.close()
        self.conn = None
    else:
      warnings.warn("SSH not connected")

  def exec(self, command: str, bufsize: int = -1, timeout: float | None = None,
           get_pty:bool = False, environment: Mapping[str, str] | None = None) -> tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]:

    if not self.conn:
      raise NotConnected()

    return self.conn.exec_command(command=command, bufsize=bufsize, timeout=timeout, 
                                    get_pty=get_pty, environment=environment)

  def pty_channel(self, term: str, height: int, width: int) -> Channel:
    if not self.conn:
      raise NotConnected()

    channel = self.conn.invoke_shell(
        term=term,
        width=width,
        height=height,
    )

    channel.settimeout(0.0)

    return channel
    
  def ssh(self, hostname, port, username=None, password=None, key_filename=None, sock=None, timeout=10):

    # Jumpbox Channel
    channel = self.transport.open_channel('direct-tcpip', (hostname, port), ('', 0), timeout = 10)

    return SSH(
      hostname=hostname, port=port, 
      username=username, password=password, 
      key_filename=key_filename, 
      sock=channel, timeout=timeout
    )

  def __call__(self, command: str, bufsize: int = -1, timeout: float | None = None,
           get_pty:bool = False, environment: Mapping[str, str] | None = None):
    return self.exec(
      command = command, 
      bufsize = bufsize, 
      timeout = timeout,
      get_pty = get_pty,
      environment = environment,
    )

  def __enter__(self, ):
    pass

  def __exit__(self, ):
    pass
  
  def __del__(self, ):
    if self.conn:
        self.conn.close()
        self.conn = None