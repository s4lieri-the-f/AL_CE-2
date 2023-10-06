import requests

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

if __name__ == "__main__":
    client = SimpleVKClient(login="Aprasidze.gera@gmail.com", password="2z5l6WhU7z!")
    client.send_message(message="тест бота", peer_id=166592935)