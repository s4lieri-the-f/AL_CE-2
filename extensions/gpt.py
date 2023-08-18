import os
import requests
import deepl
import time
import tiktoken
import requests
from langdetect import detect

import asyncio


class GPT:
    def __init__(
        self, api_token: str, api_ver: str, deepl_token: str, admins: list, log
    ) -> None:
        self.token = api_token
        self.ver = api_ver
        self.log = log
        # потом срезать
        print(self.log)
        self.deepl_token = deepl_token

        self.enc = tiktoken.get_encoding("gpt2")
        self.translator = deepl.Translator(deepl_token)
        self.models = {"3": "gpt-3.5-turbo", "4": "gpt-4"}

        self.defprompt = "alice"
        self.prompts_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "..",
                "assets",
                "extensions",
                "prompts",
            )
        )
        self.prompt = os.path.join(self.prompts_dir, f"{self.defprompt}.txt")
        self.maxtokens = 4080

        self.chat = [{"role": "system", "content": open(self.prompt).read()}]
        self.users = {}
        self.admins = admins

        return None

    def help(self) -> None:
        a = f"""Привет! Я Алиса, ваш ИИ-помощник. Чтобы меня вызвать, введите префикс - сейчас это ~ - и одну из команд ниже.
                    Я сохраняю контекст до четырех тысяч токенов -- это примерно 8 тысяч символов. Контекст тратит и запрос, и ответ, так что аккуратнее! 
                    Четвертая модель сохраняет до 8 тысяч, но она очень дорогая, аккуратно! 
                    Вот команды, которые вы можете использовать:
                    answer <запрос> - вызывает меня для ответа.
                    sysprompt <prompt_name (1 слово!)> <prompt> -- позволяет вгноять и использовать пользовательские промпты по ключу. Пока что команда доступна только администраторам.
                    reboot <ver> <name> - полностью удаляет контекст, оставляя системный промпт (если оставить имя пустым) или меняя его, а также может сменить версию модели.. Список доступных имен: \n"""
        for key in os.listdir(self.prompts_dir):
            a += "\t • " + key[:-4] + "\n"

        return a

    def tokenize(self, messages) -> int:
        total_tokens = 0
        for message in messages:
            tokens = self.enc.encode((message["content"]))
            total_tokens += len(tokens)
        return total_tokens

    def translate(self, request) -> str:
        asyncio.create_task(self.log("info", "Translating..."))
        url = "https://api-free.deepl.com/v2/translate"

        # API parameters
        params = {
            "auth_key": self.deepl_token,  # Replace with your DeepL API authentication key
            "text": request,
            "target_lang": "RU",
        }

        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            result = response.json()
            translated_text = result["translations"][0]["text"]
            return translated_text
        except requests.exceptions.RequestException as e:
            print("Error:", e)
            return None

    def gen(self, type, request) -> str:
        with open(os.path.join(self.prompts_dir, f"{type}prompt.txt"), "r") as file:
            content = file.read()

        n = self.maxtokens - self.tokenize([{"content": content}])

        messages = [
            {"role": "system", "content": content},
            {"role": "user", "content": request},
        ]  # создаем запрос

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",  # Replace with your actual API key
        }
        payload = {
            "model": self.models[self.ver],
            "messages": messages,
            "max_tokens": n,
            "n": 1,
            "stop": None,
            "temperature": 0.7,
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status()
        result = response.json()

        ai_answer = [choice["message"]["content"] for choice in result["choices"]]

        try:
            return self.translate(ai_answer)
        except:
            return ai_answer

    def message(self, user_id, name, request) -> str:
        if not user_id in self.users.keys():
            self.users[user_id] = name
        next_message = {"role": "user", "content": f"{self.users[user_id]}: {request}"}
        self.chat.append(next_message)

        n = self.maxtokens - self.tokenize(self.chat)
        while True:
            try:
                asyncio.create_task(self.log("info", f"USING {n} TOKENS FOR RESPONSE."))
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",  # Replace with your actual API key
                }
                payload = {
                    "model": self.models[self.ver],
                    "messages": self.chat,
                    "max_tokens": n,
                    "n": 1,
                    "stop": None,
                    "temperature": 0.7,
                }
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                break
            except Exception as e:
                asyncio.create_task(
                    self.log("warn", f"AL!CE CAUGHT AN ERROR: {e}. CLEARING HISTORY...")
                )
                self.chat.pop(1)
                n = self.maxtokens - self.tokenize(self.chat)

        ai_answer = result["choices"][0]["message"]["content"]
        self.chat.append({"role": "assistant", "content": ai_answer})

        if detect(ai_answer) == "en":
            ai_answer = f"[AL!CE]:{self.translate(ai_answer)}"  # Автоперевод на русский
        asyncio.create_task(
            self.log(
                "info", f"tokens left: {self.maxtokens - self.tokenize(self.chat)}"
            )
        )
        return ai_answer

    def add_admin(self, user) -> None:
        if user not in self.admins:
            self.admins.append(user)

        asyncio.create_task(self.log("info", f'Admins are: {", ".join(self.admins)}'))
        return None

    def reconfigure(self, **kwargs) -> None:  # даже блядь не пытайся
        if len(kwargs) == 0:
            self.chat = [{"role": "system", "content": open(self.prompt).read()}]
            self.log("AL!CE reloaded", time.time())
            return None

        ver = kwargs["ver"] if "ver" in kwargs.keys() else "3"
        prompt = kwargs["prompt"] if "prompt" in kwargs.keys() else self.prompt
        user = kwargs["user"] if "user" in kwargs.keys() else "admin"
        self.defprompt = prompt

        try:
            self.prompt = os.path.join(self.prompts_dir, f"{self.defprompt}.txt")
            self.chat = [{"role": "system", "content": open(self.prompt).read()}]
        except:
            asyncio.create_task(
                self.log("warn", f"Exception! Prompt {prompt} does not exist!")
            )
            return None
        if (
            user in self.admins
        ):  # Принимает на вход юзера в том числе, версии могут ребутать только админы
            if ver == "3":
                self.maxtokens = 4080
                self.ver = "3"
            elif ver == "4":
                self.maxtokens = 8180
                self.ver = "4"
            else:
                self.log("warn", f"Exception! Model {ver} does not exist!")
                return None
        else:
            self.ver = "3"

        asyncio.create_task(
            self.log(
                "info", f"Successfully switched to prompt {prompt} and gpt-ver {ver}!"
            )
        )
        return None

    def add_prompt(
        self, name: str, prompt: str, user: str
    ) -> None:  # Добавляет промпт в файл
        if user in self.admins:  # отоже могут только админы
            asyncio.create_task(
                self.log("info", f"Adding {name} prompt. Requested by admin: {user}")
            )
            with open(os.path.join(self.prompts_dir, f"{name}.txt"), "w") as file:
                file.write(
                    prompt
                    + "\n You are talking in conference, answering each user in unique way. Before every "
                    "question, there will be user's name."
                )
                os.chmod(os.path.join(self.prompts_dir, f"{name}.txt"), 0o644)
