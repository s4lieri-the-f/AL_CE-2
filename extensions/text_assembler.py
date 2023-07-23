from client import Client


def assemble(group: list, client: Client) -> tuple:
    post = f"""
        {group[1] if group[4] == "up" else ''}
        {open('./'+client.ext['pdir'], 'r', encoding='utf-8').read()}


        {'Ссылка на игру: '+ client.ext['link'] if group[2] == '1' else ''}
        {'Теги:' + group[1] if group[4] == 'down' else ''}
        """

    # возвращает ссылку, период публикации и сам пост
    return group[0], group[3], post
