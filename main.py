from client import Client, log
import os
import importlib
from inspect import iscoroutinefunction as isasync
import platform

from rich import print

# ДИТЯ ДЬЯВОЛА
import asyncio

handlers = []
commands = {}


# Will add activators() later
async def update_handlers(once=False) -> set:
    global handlers
    global commands

    while True:
        p_handlers = [*globals()["handlers"]]
        globals()["handlers"] = [
            x[:-3]
            for x in os.listdir("handlers")
            if x != "__pycache__" and x not in handlers
        ]

        if len(p_handlers) != len(globals()["handlers"]):
            to_load = [
                x
                for x in list(set(p_handlers) ^ set(globals()["handlers"]))
                if x in globals()["handlers"]
            ]
            to_unload = [
                x
                for x in list(set(p_handlers) ^ set(globals()["handlers"]))
                if x in p_handlers
            ]

            for lib in to_unload:
                del globals()[lib]

            for lib in to_load:
                try:
                    globals()[lib] = importlib.import_module("handlers." + lib)

                except Exception as e:
                    asyncio.create_task(
                        log(
                            "warn/handlers",
                            f"Caught an exception trying to load {lib} handler. Specifically: \n\t\t{e}",
                        )
                    )

                else:
                    if (
                        "COMMANDS" not in globals()[lib].__dir__()
                        or (len(globals()[lib].COMMANDS) == 0)
                        and "activator" not in globals()[lib].__dir__()
                    ):
                        asyncio.create_task(
                            log(
                                "error",
                                f"Can't see a list of activators in handlers/{lib}. Is this a handler extension?\n\t\tMoved it to /trash folder.",
                            )
                        )
                        del globals()[lib]
                        globals()["handlers"].remove(lib)
                        os.rename(f"handlers/{lib}.py", f"trash/{lib}.py")

                    elif "handle" not in globals()[lib].__dir__() or not isasync(
                        globals()[lib].handle
                    ):
                        asyncio.create_task(
                            log(
                                "error",
                                f"{lib}.handle() function if broken. Is your handler extension correct?\n\t\tMoved it to /trash folder.",
                            )
                        )
                        del globals()[lib]
                        globals()["handlers"].remove(lib)
                        os.rename(f"handlers/{lib}.py", f"trash/{lib}.py")

                    else:
                        for command in globals()[lib].COMMANDS:
                            commands[command] = lib

            if globals()["handlers"] != p_handlers and not once:
                s_handlers = "\n\t\t".join(globals()["handlers"])
                asyncio.create_task(
                    log(
                        "info",
                        f"List of handlers was modified. It is now: \n\t\t{s_handlers}",
                    )
                )
        if once:
            return handlers

        await asyncio.sleep(1)


async def update_incoming_messages(client: Client) -> None:
    global commands
    processed = {key: [] for key in client.conversations}

    while True:
        try:
            msgs = client.refresh(client.conversations)
        except Exception as e:
            asyncio.create_task(
                log(
                    "error",
                    f"Couldn't fetch messages from VK API. Exactly:\n\t\t{e}\n\n\t\tTrying again, skipping the loop.",
                )
            )
            continue

        for conf in msgs.keys():
            for msg in msgs[conf]:
                if (
                    "text" in msg.keys()
                    and len(msg["text"]) > 2
                    and msg["text"][0] == client.prefix
                    and msg["id"] not in processed[msg["peer_id"]]
                ):
                    command = msg["text"][1:].split()[0]
                    args = msg["text"].split()[1:]
                    if command not in commands.keys():
                        asyncio.create_task(
                            log(
                                "error",
                                f"No handler found for command \"{command}\". Args are: [{', '.join(args)}]. Ignoring.",
                            )
                        )
                    else:
                        msg["name"] = client.get_user(msg["from_id"])
                        asyncio.create_task(
                            log(
                                "info",
                                f"Handling \"{command}\" command with args [{', '.join(args)}] from {msg['peer_id']} id conf.\n\t\tUsing {commands[command]}.handle()",
                            )
                        )
                        print(msg)
                        try:
                            asyncio.create_task(
                                globals()[commands[command]].handle(msg, client)
                            )
                        except Exception as e:
                            asyncio.create_task(
                                log(
                                    "error",
                                    f"Handling \"{command}\" command with args [{', '.join(args)}] from {msg['peer_id']} id conf failed. Details:\n\t\t{e.args}",
                                )
                            )
                    print(command, args, sep=" ")
                    processed[msg["peer_id"]].append(msg["id"])

        for peer_id in client.conversations:
            if len(processed[peer_id]) > 10:
                processed[peer_id] = processed[peer_id][10:]
        await asyncio.sleep(1)


async def main():
    # Initiation of the main loop
    client = Client()
    machine_os = platform.system()
    asyncio.create_task(
        log(
            "info",
            f"Running on a {machine_os} machine. {'Fuck it.' if machine_os == 'Windows' else 'M.'}",
        )
    )

    globals()["handlers"] = await asyncio.create_task(update_handlers(once=True))

    s_handlers = "\n\t\t".join(globals()["handlers"])
    asyncio.create_task(
        log(
            "info",
            f"List of handlers was initially loaded. It is now: \n\t\t{s_handlers}",
        )
    )

    loop = asyncio.get_event_loop
    await asyncio.gather(update_handlers(), update_incoming_messages(client))


asyncio.run(main())
