import requests
from json import loads
import configparser
import os
from datetime import datetime as dt

class Client:
    def __init__(self) -> None:
        #reading config contents, checking if does work
        config = configparser.ConfigParser()
        config.read('assets/config.ini')
        self.name = config['INFO']['name']
        self.vk_ver = config['VK']['vk_ver']
        self.album_id = config['VK']['album_id']
        self.logon = config['VK']['login']
        self.passw = config['VK']['passw']
        self.token = config['VK']['token']

        #loading extension variables for CAME
        self.ext = config['EXTENSIONS']

        #opening a new .log file, writing into it first line, then use for it log() method
        if 'current.log' in os.listdir('logs'):
            os.rename('logs/current.log', f'logs/prev{len(os.listdir("logs"))}.log')
        with open('logs/current.log', 'w') as FILE:
            FILE.write(f'[{dt.now()} | INFO] Starting {self.name} instance via external call.')

        #check if token is expired or incorrect
        if 'error' in self.get_self().keys():
            self.log('error',
                    f'''Token is incorrect or expired, trying to get new.
                            Login: {self.logon}
                            Password: {self.passw}'''
                    )
            
            #getting new using credentials from setup
            self.token = self.login()
            config['VK']['token'] = self.token
            config.write(open('assets/key/config.ini', 'w'))

    def login(self) -> str:
        #Connecting to VK bot, logging in using
        token = loads(requests.get(
            f"https://oauth.vk.com/token?grant_type=password", 
                {
                    'grant_type': 'password',
                    'client_id': 2274003,
                    'client_secret': 'hHbZxrka2uZ6jB1inYsH',
                    'username': self.logon,
                    'password': self.passw,
                    'v': '5.131'
                }).content)
        
        if 'access_token' not in token.keys():
            self.log('fatal error', f"{token['error']['error_msg']}")

        return token['access_token']

    def refresh(self, chats: list) -> list:
        link = "https://api.vk.com/method/messages.getHistory"

        messages=[]
        for chat in chats:
            data = {'peer_id': chat,
                    'count': 10,
                    'v': self.vk_ver,
                    'access_token': self.token}
            messages.append(loads(requests.post(link, data=data).content))
        
        return messages

    def send_message(self, message: str, where: int, image=None) -> None:
        link = "https://api.vk.com/method/messages.send"
        data = {
                    'peer_id': where,
                    'message': message,
                    'random_id': 0,
                    'access_token': self.token,
                    'v': self.vk_ver
                } 
        
        if image: data['attachment'] = self.save_image(image)
        requests.post(link, data=data)
        self.log('info', f'Successfully sent message to {where} conf.')
        
    def save_image(self, image: str) -> str:
        link = "https://api.vk.com/method/photos.getUploadServer"
        data = {
                    'album_id': self.album_id,
                    'access_token': self.token,
                    'v': self.vk_ver
                }
        
        upload_link = loads(requests.post(link, data=data).content)['response']['upload_url']
        to_save = loads(requests.post(upload_link, files={'file1':open(image, 'rb')}).content)

        link = "https://api.vk.com/method/photos.save"
        data = {
                    'album_id': self.album_id,
                    'server': to_save['server'],
                    'photos_list': to_save['photos_list'],
                    'hash': to_save['hash'],
                    'aid': to_save['aid'],
                    'access_token': self.token,
                    'v': self.vk_ver
                }
        
        photo_id = loads(requests.post(link, data).content)
        self.log('info', f"Uploaded an image, id: {'photo' + str(photo_id['response'][0]['owner_id']) + '_' + str(photo_id['response'][0]['id'])}")
        return 'photo' + str(photo_id['response'][0]['owner_id']) + '_' + str(photo_id['response'][0]['id'])

    def wall_post(self, id: int, text: str) -> str:
        link = "https://api.vk.com/method/wall.post"
        data = {
                    'owner_id': id,
                    'attachments': 'photo-205064346_457239018',
                    'from_group': 1,
                    'message': text,
                    'access_token': self.token,
                    'v': self.vk_ver
                }

        result = loads(requests.post(link, data=data).content)
        self.log('info', f"Posted here: {'https://vk.com/w='+'-'+str(id)+'_'+str(result['response']['post_id'])}")
        return 'https://vk.com/w='+'-'+str(id)+'_'+str(result['response']['post_id'])
    
    
    def get_self(self) -> str:
        link = "https://api.vk.com/method/account.getProfileInfo"
        data = {
                    'access_token': self.token,
                    'v': self.vk_ver
                }       
        
        return loads(requests.post(link, data=data).content)
    
    def log(self, t: str, e: str) -> None:
        with open(f'logs/current.log', 'a') as FILE:
            FILE.write(f'\n[{dt.now()} | {t.upper()}] '+e)

    #def roll():