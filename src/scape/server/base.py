from scape.server.models import SSHSession, SSHHost, SSHCredential
from scape.server.managers import CredentialStore, HostStore, SSHSessionManager

hosts = HostStore()
credentials = CredentialStore()
sessions = SSHSessionManager(credentials, hosts)