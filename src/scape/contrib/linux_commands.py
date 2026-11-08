import re
from typing import Literal
from pathlib import Path
from scape.contrib.base import RemoteCommand
from scape.contrib.models import CommandResult, CommandSpec, DependencySpec


class SSCommand(RemoteCommand):
    def configure(self, **config):
        contrib_dir = Path(__file__).resolve().parent
        return CommandSpec(
            command="ss",
            arguments=config.get("arguments", ["-neap"]),
            sudo=config.get("sudo", False),
            timeout=15,
            dependencies=DependencySpec( supported_os=("linux", ), binaries=("ss", ), packages=("iproute2", ), ),
            serialization="textfsm",
            template_path=config.get(
                "template_path",
                contrib_dir / "templates/linux/ss_neap.textfsm",
            ),
            strict_serialization=True,
            ntc_platform="linux",
        )
    def post_execute(self, result: CommandResult):
        for index, sock_conn in enumerate(result.data):
            result.data[index]["recv_q"] = int(result.data[index]["recv_q"])
            result.data[index]["send_q"] = int(result.data[index]["send_q"])
            # result.data[index]["process"]
            # pass
        return super().post_execute(result)

class IPRouteCommand(RemoteCommand):
    def configure(self, **config):
        return CommandSpec(
            command="ip",
            arguments=config.get( "arguments", ["-j", "route", "show"], ),
            dependencies=DependencySpec( supported_os=("linux", ), binaries=("ip",), packages=("iproute2",), ),
            serialization="auto",
        )

class IPAddressCommand(RemoteCommand):
    def configure(self, **config):
        return CommandSpec(
            command="ip",
            arguments=config.get( "arguments", ["-j", "-details", "address", "show"], ),
            dependencies=DependencySpec( supported_os=("linux", ), binaries=("ip",), packages=("iproute2",), ),
            serialization="auto",
        )

class ProcessCommand(RemoteCommand):
    def configure(self, **config):
        contrib_dir = Path(__file__).resolve().parent
        return CommandSpec(
            command="ps",
            arguments=config.get("arguments", ["aux"]),
            dependencies=DependencySpec( supported_os=("linux", ), binaries=("ps",), packages=("procps",), ),
            serialization="textfsm",
            template_path=config.get(
                "template_path",
                contrib_dir / "templates/linux/ps_aux.textfsm",
            ),
            strict_serialization=True,
        )

class HostsFileCommand(RemoteCommand):
    def __init__(self, convention: Literal["Host", "IP"] | None = None, **config):
        self.convention = convention if convention else "Host"
        super().__init__(**config)

    def configure(self, **config):
        return CommandSpec(
            command="cat",
            arguments=config.get( "arguments", ["/etc/hosts"], ),
            dependencies=DependencySpec( supported_os=("linux", ), binaries=("cat",), ),
            serialization="raw",
        )

    def post_execute(self, result: CommandResult):
        old_data = result.data
        ip_to_host_map = {}
        host_to_ip_map = {}
        for hosts_line in old_data.splitlines():
            if hosts_line.strip() and not hosts_line.strip().startswith("#"):
                # Clean up the line and split it into IP and hostnames
                ip_host_map_str = hosts_line.strip()
                # Split the line into IP and hostnames using regex to handle multiple spaces
                ip_host_map_lst = re.split(r'\s+', ip_host_map_str)
                # The first element is the IP address, and the rest are hostnames
                ip = ip_host_map_lst[0]
                hosts = ip_host_map_lst[1:]

                # Create a mapping of IP to hostnames and hostnames to IP
                ip_to_host_map[ip] = hosts

                # Create a mapping of hostnames to IP
                for host in hosts:
                    host_to_ip_map[host] = ip

        if self.convention == "Host":
            result.data = host_to_ip_map
        elif self.convention == "IP":
            result.data = ip_to_host_map
        else:
            raise Exception("Invalid convention. Must be 'Host' or 'IP'.")

        return super().post_execute(result)
