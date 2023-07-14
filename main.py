from client import Client

def main():
    client = Client()
    log = \
f"""
    INFO:
        Name: {client.name}

    VK:
        API ver.: {client.vk_ver}
        Credentials: {client.logon}:{client.passw}
        Token: {client.token}

    EXTENSIONS VARIABLES:"""
    for key in client.ext.keys():
            log += "\n\t\t" + key.upper().replace('_', ' ').replace('api', 'API') + ": " + client.ext[key]
    client.log('info', log)

main()