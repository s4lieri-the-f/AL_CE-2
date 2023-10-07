import requests
from json import loads
import os

class SimpleVKClient:
    def __init__(self, token: str, vk_ver: str = "5.131"):
        self.vk_ver = vk_ver
        self.token = token

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

    def create_album(self, title):
        link = "https://api.vk.com/method/photos.createAlbum"
        data = {
            "title": title,
            "privacy": 3
        }
        response = loads(requests.post(link, data=data).content)
        return response["response"]["id"]

    def save_image(self, image, album_id: str) -> str:
        link = "https://api.vk.com/method/photos.getUploadServer"
        data = {"album_id": album_id, "access_token": self.token, "v": self.vk_ver}

        upload_link = loads(requests.post(link, data=data).content)["response"][
            "upload_url"
        ]

        with open('tmp.jpg', 'wb') as FILE:
            FILE.write(image)

        to_save = loads(
            requests.post(
                upload_link, files={"file1": open("tmp.jpg", 'rb')}
            ).content
        )
        os.remove('tmp.jpg')



        link = "https://api.vk.com/method/photos.save"
        data = {
            "album_id": album_id,
            "server": to_save["server"],
            "photos_list": to_save["photos_list"],
            "hash": to_save["hash"],
            "aid": to_save["aid"],
            "access_token": self.token,
            "v": self.vk_ver,
        }

        photo_id = loads(requests.post(link, data).content)
        print(photo_id)
        return (
            "photo"
            + str(photo_id["response"][0]["owner_id"])
            + "_"
            + str(photo_id["response"][0]["id"])
        )

    def wall_post(self, id: int, text: str, image_id) -> str:
        link = "https://api.vk.com/method/wall.post"
        data = {
            "owner_id": id,
            "attachments": image_id,
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

