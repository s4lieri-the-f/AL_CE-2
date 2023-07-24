from client import Client, log
from extensions.gpt import *

# ДИТЯ ДЬЯВОЛА
import asyncio

# Mandatory variables list
COMMANDS = ["gen", "asnwer", "reboot"]


# Function, using Client() to return requested result.
async def handle(msg: dict, client: Client) -> None:
    client.gpt_client = (
        GPT(client.ext["openai_key"], "3", client.ext["deepl_api"], log)
        if "gpt_client" not in client.__dir__()
        else client.gpt_client
    )

    return
