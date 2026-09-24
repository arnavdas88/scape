# The Scape Agent

The scape agent

# Install

```sh
pip install git+https://github.com/arnavdas88/scape
```

# Use as a package 

Import scape 
```py
import io
from scape.ssh import SSH, detect_key_crypto
```

Load the private key
```py
pem_obj = io.StringIO( open("private.key", "r").read() )
KeyCryptoScheme = detect_key_crypto(pem_obj)
pub_key = KeyCryptoScheme.from_private_key(pem_obj)
```

Create the host connections
```py
host_a = SSH(hostname = "xxx.xxx.xxx.xxx", port=22, username="user_a", pkey=pub_key)
host_b = host_a.ssh(hostname = "yyy.yyy.yyy.yyy", port=22, username="user_b", password="SomePassword")
host_c = host_b.ssh(hostname = "zzz.zzz.zzz.zzz", port=22, username="user_c", password="AnotherPassword")
```

Execute commands
```py
stdin, stdout, stderr = host_a("ip addr")
host_a_output = stdout.readlines()
print(host_a_output)

stdin, stdout, stderr = host_b("ip addr")
host_b_output = stdout.readlines()
print(host_b_output)

stdin, stdout, stderr = host_c("ip addr")
host_c_output = stdout.readlines()
print(host_c_output)
```
