import io

from scape.ssh import SSH, detect_key_crypto

def main():
    pem_obj = io.StringIO(
        open("private.key", "r").read()
    )

    KeyCrypto = detect_key_crypto(pem_obj)

    if KeyCrypto:
        pub_key = KeyCrypto.from_private_key(pem_obj)

        host_a = SSH(hostname = "xxx.xxx.xxx.xxx", port=22, username="user_a", pkey=pub_key)
        host_b = host_a.ssh(hostname = "yyy.yyy.yyy.yyy", port=22, username="user_b", password="SomePassword")
        host_c = host_b.ssh(hostname = "zzz.zzz.zzz.zzz", port=22, username="user_c", password="AnotherPassword")


        stdin, stdout, stderr = host_a("ip addr")
        host_a_output = stdout.readlines()
        print(host_a_output)

        stdin, stdout, stderr = host_b("ip addr")
        host_b_output = stdout.readlines()
        print(host_b_output)

        stdin, stdout, stderr = host_c("ip addr")
        host_c_output = stdout.readlines()
        print(host_c_output)

if __name__ == "__main__":
    main()