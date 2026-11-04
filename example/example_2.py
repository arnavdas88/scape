import io
import json
import ipaddress
from sys import stdout

from paramiko import AuthenticationException
from scape.ssh import SSH, detect_key_crypto

def main():
    HOSTS = []
    NETWORKS = []
    CREDENTIALS = [ 
        { "username": "user_a", "password": "SomePassword", }, 
        { "username": "user_b", "password": "AnotherPassword", } 
    ]

    HOSTS_SCAN_PENDING = [ 
        ipaddress.IPv4Address("xxx.xxx.xxx.xxx") 
    ]

    while len(HOSTS_SCAN_PENDING):
        _host = HOSTS_SCAN_PENDING.pop()
        HOSTS.append(_host)

        _ssh_host = None

        # Bruteforce credentials
        for _creds in CREDENTIALS:
            try:
                _ssh_host = SSH(hostname=str(_host), port=22, username=_creds["username"], password=_creds["password"])
            except AuthenticationException as e:
                _ssh_host = None
                continue

        if not _ssh_host:
            print(f"Unable to connect to {_host} with provided credentials.")
            continue

        # Get host keys
        _host_keys = _ssh_host.host_keys

        stdin, stdout, stderr = _ssh_host("whoami")
        host_user = stdout.readlines().pop().strip("\n")

        stdin, stdout, stderr = _ssh_host("ip -j addr")
        host_networks = json.loads(stdout.readlines().pop())

        host_network_dict = {_network['ifname']:_network['addr_info'][0].get('local') for _network in host_networks if _network['addr_info'] }
        for ifname, local_ip in host_network_dict.items():

            if ifname == "lo":
                # Skip Localhost
                continue

            _host_iface_ip = ipaddress.IPv4Address(local_ip)

            _host_iface_ip_network = ipaddress.IPv4Network(f"{_host_iface_ip}/24", strict=False)
            if _host_iface_ip_network not in NETWORKS:
                NETWORKS.append(_host_iface_ip_network)
            else:
                continue

            # Scan the entire network using ping command
            for _index, _new_host in enumerate(_host_iface_ip_network.hosts()):
                # if _index < 1 or _index > 21:
                #     # Only Select the 2nd to 20th hosts for scanning to avoid flooding the network
                #     continue

                # Check Aliveness
                stdin, stdout, stderr = _ssh_host(f"ping -c 1 -W 1 {str(_new_host)}")
                network_hosts_ping = stdout.readlines()
                is_host_alive = "1 received" in network_hosts_ping[-2]

                if is_host_alive and _new_host not in HOSTS:
                    HOSTS_SCAN_PENDING.append(_new_host)

        pass
    
    print(f"Hosts: {HOSTS}")
    print(f"Networks: {NETWORKS}")



if __name__ == "__main__":
    main()