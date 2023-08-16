import requests
from json import loads
import configparser
import os
from datetime import datetime as dt

# ДИТЯ ДЬЯВОЛА
import asyncio


class Client:
    def __init__(self) -> None:
        # reading config contents, checking if does work
        config = configparser.ConfigParser()
        config.read("assets/config.ini")
        self.name = config["INFO"]["name"]
        self.prefix = config["INFO"]["prefix"]
        self.vk_ver = config["VK"]["vk_ver"]
        self.album_id = config["VK"]["album_id"]
        self.logon = config["VK"]["login"]
        self.passw = config["VK"]["passw"]
        self.token = config["VK"]["token"]
        self.conversations = loads(config["VK"]["conversations"])

        # loading extension variables for CAME
        self.ext = dict(config["EXTENSIONS"])
        print(self.ext)

        # opening a new .log file, writing into it first line, then use for it log() method
        if "logs" not in os.listdir():
            os.mkdir("logs")

        if "current.log" in os.listdir("logs"):
            os.rename("logs/current.log", f'logs/prev{len(os.listdir("logs"))}.log')
        with open("logs/current.log", "w") as FILE:
            FILE.write(
                f'[{dt.now()} | INFO] Starting {self.name} instance via external call.\n\t\tCommand prefix is "{self.prefix}"'
            )

        # getting new using credentials from setup
        if not self.token:
            self.token = self.login()
            config["VK"]["token"] = self.token
            config.write(open("assets/config.ini", "w"))

        # finally logging
        log_message = f"""
        {self.name} variables are:
                VK API ver.: {self.vk_ver}
                Login: {self.logon}
                Password: {self.passw}
                Token: {self.token}
                Prefix: {self.prefix}
                Album ID: {self.album_id}
                Conversation ID's: {self.conversations}"""
        asyncio.create_task(log("info", log_message))

    def login(self) -> str:
        # Connecting to VK bot, logging in using
        token = loads(
            requests.get(
                f"https://oauth.vk.com/token?grant_type=password",
                {
                    "grant_type": "password",
                    "client_id": 2274003,
                    "client_secret": "hHbZxrka2uZ6jB1inYsH",
                    "username": self.logon,
                    "password": self.passw,
                    "v": "5.131",
                },
            ).content
        )

        return token["access_token"]

    def get_user(self, from_id: int) -> str:
        name = loads(
            requests.post(
                f"https://api.vk.com/method/users.get",
                {
                    "v": self.vk_ver,
                    "access_token": self.token,
                    "user_ids": [from_id],
                    "name_case": "nom",
                },
            ).content
        )["response"][0]
        return name["first_name"] + " " + name["last_name"]

    def get_user_number_id(self, tag: str) -> str: #Получает цифровой айди юзера из тега
        response = loads(
            requests.post(
                f"https://api.vk.com/method/users.get",
                {
                    "v": self.vk_ver,
                    "access_token": self.token,
                    "user_ids": [tag],
                    "name_case": "nom",
                },
            ).content
        )
        if "response" in response:
            return response["response"][0]["id"]

    def refresh(self, chats: list) -> list:
        link = "https://api.vk.com/method/messages.getHistory"

        messages = {}
        for chat in chats:
            data = {
                "peer_id": chat,
                "count": 10,
                "v": self.vk_ver,
                "access_token": self.token,
            }

            messages[chat] = loads(requests.post(link, data=data).content)
            if "response" not in messages[chat].keys():
                asyncio.create_task(
                    log(
                        "error",
                        f"Something went wrong while fetching conversations. Exactly:\n\t\t{messages[chat]}",
                    )
                )
                return
            else:
                messages[chat] = messages[chat]["response"]["items"]
        return messages

    def send_message(self, message: str, where: int, image=None, reply=None) -> None:
        asyncio.create_task(
            log("info", f"Sending message to {where} conf. Text:\n\t\t{message}")
        )
        link = "https://api.vk.com/method/messages.send"
        data = {
            "peer_id": where,
            "message": message,
            "random_id": 0,
            "access_token": self.token,
            "v": self.vk_ver,
        }
        if reply:
            data["reply_to"] = reply

        if image:
            data["attachment"] = self.save_image(image)
        r = loads(requests.post(link, data=data).content.decode())
        if "error" in r.keys():
            asyncio.create_task(
                log(
                    "error",
                    f"Caught an error while trying to send message. Specificaly:\n\t\t{r['error']['error_code']}: {r['error']['error_msg']}",
                )
            )

    def save_image(self, path_to_image: str) -> str:
        link = "https://api.vk.com/method/photos.getUploadServer"
        data = {"album_id": self.album_id, "access_token": self.token, "v": self.vk_ver}

        upload_link = loads(requests.post(link, data=data).content)["response"][
            "upload_url"
        ]
        to_save = loads(
            requests.post(
                upload_link, files={"file1": open(path_to_image, "rb")}
            ).content
        )

        link = "https://api.vk.com/method/photos.save"
        data = {
            "album_id": self.album_id,
            "server": to_save["server"],
            "photos_list": to_save["photos_list"],
            "hash": to_save["hash"],
            "aid": to_save["aid"],
            "access_token": self.token,
            "v": self.vk_ver,
        }

        photo_id = loads(requests.post(link, data).content)
        return (
            "photo"
            + str(photo_id["response"][0]["owner_id"])
            + "_"
            + str(photo_id["response"][0]["id"])
        )

    def wall_post(self, id: int, text: str, path_to_img: str) -> str:
        link = "https://api.vk.com/method/wall.post"
        data = {
            "owner_id": id,
            "attachments": self.save_image(path_to_img),
            "from_group": 1,
            "message": text,
            "access_token": self.token,
            "v": self.vk_ver,
        }

        result = loads(requests.post(link, data=data).content)
        return (
            "https://vk.com/w="
            + "-"
            + str(id)
            + "_"
            + str(result["response"]["post_id"])
        )

    def get_self(self) -> str:
        link1 = "https://api.vk.com/method/account.getProfileInfo"
        link2 = "https://api.vk.com/method/messages.getConversations"
        link3 = "https://api.vk.com/method/messages.getConversationsById"
        data = {"access_token": self.token, "v": self.vk_ver}

        self_data = loads(requests.post(link1, data=data).content)
        conversations = loads(
            requests.post(link2, data={**data, "filter": "all"}).content
        )

        self_conversations = {}
        for conf in conversations["response"]["items"]:
            name = loads(
                requests.post(
                    link3, data={**data, "peer_ids": conf["conversation"]["peer"]["id"]}
                ).content
            )
            print(name)

        # response, items

        return {**self_data, **self_conversations}


async def log(itype: str, text: str) -> None:
    with open("logs/current.log", "a", encoding="utf-8") as FILE:
        FILE.write(f"\n[{dt.now()} | {itype.upper()}] {text}")
    return
