import requests
from json import loads

class SimpleVKClient:
    def __init__(self, login: str, password: str, vk_ver: str = "5.131"):
        self.vk_ver = vk_ver
        self.login = login
        self.password = password
        self.token = self.login_to_vk()

    def login_to_vk(self) -> str:
        response = requests.get(
            "https://oauth.vk.com/token?grant_type=password",
            params={
                "grant_type": "password",
                "client_id": 2274003,
                "client_secret": "hHbZxrka2uZ6jB1inYsH",
                "username": self.login,
                "password": self.password,
                "v": self.vk_ver,
            },
        )
        token_data = response.json()
        print(token_data)
        # Если требуется двухфакторная аутентификация
        if token_data.get('error') == 'need_validation':
            code = input('Enter 2FA code: ')
            validation_sid = token_data['validation_sid']
            params = {
                "grant_type": "password",
                "client_id": 2274003,
                "client_secret": "hHbZxrka2uZ6jB1inYsH",
                "username": self.login,
                "password": self.password,
                "code": code,
                "validation_sid": validation_sid,
                "v": self.vk_ver
            }
            # Дополнительный запрос для завершения 2FA
            response = requests.get("https://oauth.vk.com/token?grant_type=password", params=params)
            token_data = response.json()
            print(token_data)
        return token_data.get("access_token", "")

    def send_message(self, message: str, peer_id: int) -> None:
        link = "https://api.vk.com/method/messages.send"
        data = {
            "peer_id": peer_id,
            "message": message,
            "random_id": 0,
            "access_token": self.token,
            "v": self.vk_ver,
        }
        response = requests.post(link, data=data)
        # Если нужно обработать ответ от VK API, делаем это тут

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

