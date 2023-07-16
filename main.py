from client import Client
import os
import importlib


def main():
    client = Client()
    log = f"""
    INFO:
        Name: {client.name}

    VK:
        API ver.: {client.vk_ver}
        Credentials: {client.logon}:{client.passw}
        Token: {client.token}

    EXTENSIONS VARIABLES:"""
    for key in client.ext.keys():
        log += (
            "\n\t\t"
            + key.capitalize().replace("_", " ").replace("api", "API")
            + ": "
            + client.ext[key]
        )
    client.log("info", log)

    handlers = [x[:-3] for x in os.listdir("handlers") if x != "__pycache__"]
    client.log(
        "info",
        f"There are {len(handlers)} handlers in the /handlers folder. \n\t\tThey are: {', '.join(handlers)}.\n\t\tNow will check if conditions are colliding.",
    )

    for handler in handlers:
        globals()[handler] = importlib.import_module("handlers." + handler)


main()
