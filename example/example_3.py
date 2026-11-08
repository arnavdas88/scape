import io

from scape.ssh import SSH, detect_key_crypto
from scape.contrib.linux_commands import SSCommand, ProcessCommand
from scape.contrib.linux_commands import IPRouteCommand, IPAddressCommand
from scape.contrib.linux_commands import HostsFileCommand

def main():
    host_a = SSH(hostname = "xxx.xxx.xxx.xxx", port=22, username="user_a", password="SomePassword")
    host_b = host_a.ssh(hostname = "yyy.yyy.yyy.yyy", port=22, username="user_b", password="AnotherPassword")

    # Running commands manually on a remote host
    stdin, stdout, stderr = host_b("whoami")
    user_whoami_output = stdout.readlines()

    stdin, stdout, stderr = host_b("whoami", sudo=True)
    sudo_whoami_output = stdout.readlines()


    # Running through the command interface on a remote host
    ip_addr_command = IPAddressCommand()
    ss_command = SSCommand(sudo=True, )
    ps_command = ProcessCommand()
    ip_route_command = IPRouteCommand()
    hosts_command = HostsFileCommand(convention="IP")

    ip_addr_result = ip_addr_command.execute(host_b)
    ss_result = ss_command.execute(host_b)
    ps_result = ps_command.execute(host_b)
    ip_route_result = ip_route_command.execute(host_b)
    hosts_result = hosts_command.execute(host_b)

    pass

if __name__ == "__main__":
    main()