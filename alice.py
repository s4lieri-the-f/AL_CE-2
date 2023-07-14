import asyncio
from login import login
from rich import print as rprint
import time
from datetime import datetime
import requests
from json import loads, dumps
from gptAPI import *
import subprocess

vk_ver = 5.131
chat_ver = "3"

answered_temple = []
answered_slayers = []

async def temple():
    token = login()
    rprint('[bold green]LOGGED IN')
    
    i = 0
    while True:
        i += 1
        await asyncio.gather(bot(token), carnage(token))

        if i%10000 == 0:
            i = 0
            answered_slayers = []
            answered_temple = []
        
        await asyncio.sleep(3)

async def bot(token):
    result = loads(requests.get(f"https://api.vk.com/method/messages.getHistory?peer_id=2000000011&count=7&access_token={token}&v={vk_ver}").content.decode())
    
    if 'response' in result.keys(): 
        for message in result['response']['items']:
            if message['text'] != '' and message['id'] not in answered_slayers and message['text'][0] == '#':
                answered_slayers.append(message['id'])
                atime = datetime.now().strftime("[%H:%M:%S]")
                text = "[AL!CE] Something unexpected occured."
                requests.post(f"https://api.vk.com/method/messages.send?peer_id=2000000011&random_id=0&reply_to={message['id']}&access_token={token}&v={vk_ver}", data={'message': 'Обрабатываю.'}).content
                if message['text'][1:].split(' ')[0] in prompts.keys():
                    text, atime = generate(message['text'][1:].split(' ')[0], ' '.join(message['text'].split()[1:]))
                elif message['text'][1:7].lower() == 'reboot':
                    print(message['text'].lower().split('reboot')[1])
                    try:
                        reload(' '.join(message['text'].split()[1:]))
                    except:
                        reload()
                    text = "[AL!CE] Reloaded."  
                elif message['text'][1:6].lower() == 'flush':
                    try:
                        text = flush(int(message['text'].lower().split(' ')[1]))
                    except:
                        text = flush(1)
                elif message['text'][1:6].lower() == 'guide':
                    text = guide()
                elif message['text'][1:4].lower() == 'ans':
                    text, atime = chat(message['text'].lower().split('ans')[1], gptmodel=chat_ver)
                elif message['text'][1:8].lower() == 'wolfram':
                    eqtype = ''
                    for item in ['=', '<', '>', '>=', '<=', '!=']:
                        if item in message['text'].lower():
                            eqtype = 'eq'
                            break
                    text, atime = wolframalpha(''.join(message['text'].lower().split('wolfram')[1]), etype=eqtype)
                    text = "\n\n".join(text)
                requests.post(f"https://api.vk.com/method/messages.send?peer_id=2000000011&random_id=0&reply_to={message['id']}&access_token={token}&v={vk_ver}", data={'message': translate(atime+'\n\n'+text)}).content

async def carnage(token):
    global chat_ver
    result = loads(requests.get(f"https://api.vk.com/method/messages.getHistory?peer_id=2000000010&count=7&access_token={token}&v={vk_ver}").content.decode())
    
    text = ''
    if 'response' in result.keys(): 
        for message in result['response']['items']:
            if message['text'] != '' and message['id'] not in answered_temple:
                answered_temple.append(message['id'])
                if '*karuizawalice' in message['text'] or '@karuizawalice' in message['text']:
                    atime = str(round(time.time(), 3))
                    if 'reboot' in message['text'].lower():
                        msg = message['text'].lower().replace('[id608981031|*karuizawalice]', '').replace('[id608981031|@karuizawalice]', '').split()
                        try:
                            reload(' '.join(msg[1:]))
                        except:
                            reload()
                        text = "[AL!CE] Reloaded."  
                    elif 'flush' in message['text'].lower():
                        text = flush(int(message['text'].lower().split(' ')[2]))
                    elif "aliceguide" in message['text'].lower():
                        text = guide()
                    elif 'sysprompt' in message['text'].lower():
                        try:
                            key = message['text'].lower().replace('[id608981031|*karuizawalice]', '').replace('[id608981031|@karuizawalice]', '').split()
                            rprint(system_prompts)
                            add_system(key[1], ' '.join(key[2:]))
                            text = f"[AL!CE] {key[1]} prompt added to pool! Until full reboot, however."
                        except:
                            text = "[AL!CE] Fuck this shit."
                    elif 'wolfram' in message['text'].lower():
                        eqtype = ''
                        for item in ['=', '<', '>', '>=', '<=', '!=']:
                            if item in message['text'].lower():
                                eqtype = 'eq'
                                break
                        text, atime = wolframalpha(''.join(message['text'].lower().split('wolfram')[1]), etype=eqtype)
                        text = "\n\n".join(text)
                    elif 'ver' in message['text'].lower():
                        nv = message['text'].lower().split()[-1]
                        if nv in ["3", "4"]:
                            chat_ver = nv
                            text = f"[AL!CE] Successfully switched to the {nv} ver."
                        else:
                            text = "You're fucker. Check and choose the existing api version."
                    else:
                        requests.post(f"https://api.vk.com/method/messages.send?peer_id=2000000010&random_id=0&reply_to={message['id']}&access_token={token}&v={vk_ver}", data={'message': 'Обрабатываю.'}).content
                        text, atime = chat(message['text'].replace(',', '').replace('[id608981031|*karuizawalice]', '').replace('[id608981031|@karuizawalice]', ''), gptmodel=chat_ver)
                        text = translate(text)
                    
                    requests.post(f"https://api.vk.com/method/messages.send?peer_id=2000000010&random_id=0&reply_to={message['id']}&access_token={token}&v={vk_ver}", data={'message': atime+'\n\n'+text}).content

asyncio.run(temple())