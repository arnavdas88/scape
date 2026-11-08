import io

from scape.ssh import SSH, detect_key_crypto
from scape.contrib.linux_commands import SSCommand, ProcessCommand
from scape.contrib.linux_commands import IPRouteCommand, IPAddressCommand
from scape.contrib.linux_commands import HostsFileCommand

def main():
    host_a = SSH(hostname = "xxx.xxx.xxx.xxx", port=22, username="user_a", password="SomePassword")

    stdin, stdout, stderr = host_a("whoami")
    user_whoami_output = stdout.readlines()

    stdin, stdout, stderr = host_a("whoami", sudo=True)
    sudo_whoami_output = stdout.readlines()

    ip_addr_command = IPAddressCommand()
    ip_addr_result = ip_addr_command.execute(host_a)

    ss_command = SSCommand(sudo=True, )
    ss_result = ss_command.execute(host_a)

    ps_command = ProcessCommand()
    ps_result = ps_command.execute(host_a)

    ip_route_command = IPRouteCommand()
    ip_route_result = ip_route_command.execute(host_a)

    hosts_command = HostsFileCommand(convention="IP")
    hosts_result = hosts_command.execute(host_a)

    pass

if __name__ == "__main__":
    main()