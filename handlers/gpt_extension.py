from client import Client, log
from extensions.gpt import *

# ДИТЯ ДЬЯВОЛА
import asyncio

# Mandatory variables list
COMMANDS = ["gen", "answer", "reboot", "help", "sysprompt"]


# Function, using Client() to return requested result.
async def handle(msg: dict, client: Client) -> None:
    client.gpt_client = (
        GPT(client.ext["openai_key"], "3", client.ext["deepl_api"], log)
        if "gpt_client" not in client.__dir__()
        else client.gpt_client
    )

    text = msg["text"]
    peer_id = msg["peer_id"]
    user_id = msg["from_id"]
    name = msg["name"]
    reply_id = msg["id"]
    prefix = client.prefix

    if any(prefix + com in text for com in COMMANDS):
        command = text.split()[0][1:]
        request = text[len(command) :]
        asyncio.create_task(
            log(
                "info",
                f'GPT is processing "{command}" command with "{request}" request.',
            )
        )
        if command == "answer":
            response = client.gpt_client.message(user_id, name, request)
            asyncio.create_task(log("info", f'Generated response: "{response}"'))
            client.send_message(response, peer_id, None, reply_id)
            return
        elif command == "gen":
            type = text.split()[1]
            request = text[len(command) + len(type) :]
            response = client.gpt_client.gen(type, request)
            asyncio.create_task(log("info", f'Generated response: "{response}"'))
            client.send_message(response, peer_id, None, reply_id)
            return
        elif command == "reboot":
            request = text[len(command) :]
            if len(request) < 3:
                client.gpt_client.reconfigure()
            if " 4 " in request:
                ver = "4"
            else:
                ver = "3"
            prompt = request.split()[0]
            client.gpt_client.reconfigure(ver=ver, prompt=prompt)
            asyncio.create_task(
                log(
                    "info",
                    f"GPT was reconifgured. Current settings:\n\t\tver.: {ver}\n\t\Prompt: {prompt}",
                )
            )
        elif command == "sysprompt":
            name = request.split()[0]
            prompt = request[len(name) :]
            client.gpt_client.addprompt(name, prompt)
        elif command == "help":
            client.send_message(client.gpt_client.help(), peer_id, reply=reply_id)

    return
