import os
import sqlite3
from rich import print

class Ad():
    def __init__(self, database):
        self.database = database

    def _execute_query(self, query, params=(), commit=False):
        """
        Выполняет SQL-запрос и возвращает результат.

        :param query: SQL-запрос для выполнения
        :param params: Параметры для SQL-запроса
        :param commit: Нужно ли подтверждать транзакцию (для операций INSERT/UPDATE/DELETE)
        :return: Результат запроса
        """
        with sqlite3.connect(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
            else:
                return cursor.fetchall()

    def get_all_user_groups(self):
        query = "SELECT * FROM UserGroups"
        groups = self._execute_query(query)
        print("[bold]User Groups:[/bold]")
        print(groups)
        return  groups

    def get_user_group_link(self, user_id):
        # Предполагается, что у вас есть таблица UserGroups с полями id и link
        query = "SELECT link FROM UserGroups WHERE id = ?"
        result = self._execute_query(query, (user_id,))
        return result[0][0] if result else None

    def get_user_group_id(self, user_id):
        query = "SELECT group_id FROM Users WHERE id = ?"
        result = self._execute_query(query, (user_id,))
        return result[0][0] if result else None

    def get_ad_posts(self, group_id):
        query = "SELECT content FROM UserGroupPosts WHERE user_group_id = ?"
        results = self._execute_query(query, (group_id,))
        return [result[0] for result in results]

    def get_ad_groups(self, group_id):
        query = "SELECT ad_group_id FROM UserGroupAdGroup WHERE user_group_id = ?"
        results = self._execute_query(query, (group_id,))
        return [result[0] for result in results]

    def get_user_group_and_posts(self, group_id):
        query = "SELECT * FROM UserGroupPosts WHERE user_group_id = ?"
        posts = self._execute_query(query, (group_id,))
        print(f"[bold]Posts for User Group {group_id}:[/bold]")
        print(posts)
        return posts
    
    def get_post_by_id(self, post_id):
        query = "SELECT content FROM UserGroupPosts WHERE id = ?"
        post = self._execute_query(query, (post_id,))
        return post

    def get_user_group_and_hashtags(self, group_id):
        query = "SELECT hashtags FROM UserGroups WHERE id = ?"
        hashtags = self._execute_query(query, (group_id,))
        print(f"[bold]Hashtags for User Group {group_id}:[/bold]")
        print(hashtags)
        return hashtags

    def get_user_group_and_ad_groups(self, group_id):
        query = """
        SELECT AdGroups.* FROM AdGroups
        JOIN UserGroupAdGroup ON AdGroups.id = UserGroupAdGroup.ad_group_id
        WHERE UserGroupAdGroup.user_group_id = ?
        """
        ad_groups = self._execute_query(query, (group_id,))
        print(f"[bold]Ad Groups for User Group {group_id}:[/bold]")
        print(ad_groups)
        return ad_groups

    def get_all_ad_groups(self):
        query = "SELECT * FROM AdGroups"
        ad_groups = self._execute_query(query)
        print("[bold]Ad Groups:[/bold]")
        print(ad_groups)
        return ad_groups

    def get_ad_group(self, ad_group_id):
        query = "SELECT * FROM AdGroups WHERE id = ?"
        ad_group = self._execute_query(query, (ad_group_id,))
        print(f"[bold]Ad Group {ad_group_id}:[/bold]")
        print(ad_group)
        return  ad_group

    def associate_ad_group_db(self, ad_group_id, user_group_id):
        query = "INSERT INTO UserGroupAdGroup (user_group_id, ad_group_id) VALUES (?, ?)"
        self._execute_query(query, (user_group_id, ad_group_id), commit=True)
        print(f"[bold]Added assosiacion for  User Group {user_group_id} and ad group: {ad_group_id}[/bold]")
        return True

    def delete_association_db(self, ad_group_id, user_group_id):
        query = "DELETE FROM UserGroupAdGroup WHERE user_group_id = ? AND ad_group_id = ?"
        self._execute_query(query, (user_group_id, ad_group_id), commit=True)
        print(f"[bold]Deleted assosiacion for  User Group {user_group_id} and ad group: {ad_group_id}[/bold]")
        return True

    def add_post_image(self, group_id, image_path):
        # Чтение изображения в виде бинарных данных
        with open(image_path, 'rb') as file:
            image_data = file.read()

        query = "INSERT INTO PostImages (group_id, image) VALUES (?, ?, ?)"
        self._execute_query(query, (group_id, image_data), commit=True)
        print(f"[bold]Added image for Group ID: {group_id}[/bold]")

    def delete_all_syncs_for_post(self, post_id):
        query = "DELETE FROM ImagesSync WHERE post_id = ?"
        self._execute_query(query, (post_id,), commit=True)
    def add_post_image_sync(self, post_id, image_id):
        query = "SELECT * FROM ImagesSync WHERE post_id = ? AND image_id = ?"
        result = self._execute_query(query, (post_id, image_id))
        if len(result)<=0:
            query = "INSERT INTO ImagesSync (post_id, image_id) VALUES (?, ?)"
            self._execute_query(query, (post_id, image_id), commit=True)
        return True

    def get_post_images(self, post_id):
        query = """
            SELECT PostImages.id, PostImages.image
            FROM PostImages 
            JOIN ImagesSync ON PostImages.id = ImagesSync.image_id 
            WHERE ImagesSync.post_id = ?
            """
        images = self._execute_query(query, (post_id,))
        return [image for image in images]

    def get_group_images(self, group_id):
        query = "SELECT id, image FROM PostImages WHERE group_id = ?"
        images = self._execute_query(query, (group_id,))
        return [image for image in images]

    def save_image_to_file(self, image_data, file_path):
        with open(file_path, 'wb') as file:
            file.write(image_data)

    def update_user_group(self, group_id, new_link):
        query = "UPDATE UserGroups SET link = ? WHERE id = ?"
        self._execute_query(query, (new_link, group_id), commit=True)
        print(f"[bold]Updated User Group {group_id} with new link: {new_link}[/bold]")

    def update_post(self, post_id, post_content):
        query = "UPDATE UserGroupPosts SET content = ? WHERE id = ?"
        self._execute_query(query, (post_content, post_id), commit=True)


    def validate_key(self, user_key):
        query = "SELECT id FROM Users WHERE access_code = ?"
        result = self._execute_query(query, (user_key,))
        if result:
            return result[0][0]  # Return the user ID
        else:
            return None

    def add_user_group(self, link):
        query = "INSERT INTO UserGroups (link) VALUES (?)"
        self._execute_query(query, (link,), commit=True)
        print(f"[bold]Added User Group with link: {link}[/bold]")

    def add_ad_group(self, link, allowed_hashtags, is_link_allowed, period, row_type):
        query = """
            INSERT INTO AdGroups (link, allowed_hashtags, is_link_allowed, period, row_type) 
            VALUES (?, ?, ?, ?, ?)
        """
        self._execute_query(query, (link, allowed_hashtags, is_link_allowed, period, row_type), commit=True)
        print(f"[bold]Added Ad Group with link: {link}[/bold]")

    def add_post(self, user_group_id, post_text):
        query = """
            INSERT INTO UserGroupPosts (user_group_id, post_text) 
            VALUES (?, ?)
        """
        self._execute_query(query, (user_group_id, post_text), commit=True)
        print(f"[bold]Added Post for User Group ID: {user_group_id}[/bold]")

    def add_usergroup_adgroup_relations(self, user_group_id, ad_group_ids):
        # Подготовка данных для вставки
        values_to_insert = [(user_group_id, ad_group_id) for ad_group_id in ad_group_ids]

        # Вставка данных в таблицу
        query = "INSERT INTO UserGroupAdGroup (user_group_id, ad_group_id) VALUES (?, ?)"
        with sqlite3.connect(self.database) as conn:
            cursor = conn.cursor()
            cursor.executemany(query, values_to_insert)
            conn.commit()

        print(f"[bold]Added relations for User Group ID: {user_group_id} with Ad Group IDs: {ad_group_ids}[/bold]")

    def assemble(self, user_group_id, ad_group_id, post_id):
        ad_group = self.get_ad_group(ad_group_id)[0]
        # Получаем данные о посте
        post_query = "SELECT * FROM UserGroupPosts WHERE id = ? AND user_group_id = ?"
        post = self._execute_query(post_query, (post_id, user_group_id))[0]

        # Проверяем, есть ли пост для данной группы пользователя
        if not post:
            raise ValueError("No post found for the provided user group ID and post ID.")
        #получаем картинку для поста
        image_bytes = self.get_post_images(post_id)
        # Собираем пост
        assembled_post = ""
        posttext = post[2]  # Текст поста
        link = ad_group[1]  # Ссылка из рекламной группы
        hashtags = ad_group[2]  # Хештеги из рекламной группы
        is_link_allowed = ad_group[3]  # Разрешена ли ссылка
        row_type = ad_group[5]  # Тип строки: 'up' или 'down'

        # Добавляем хештеги и ссылку в соответствии с требованиями
        if row_type == "up":
            assembled_post += "Теги: \n" + hashtags + "\n" + posttext
            if is_link_allowed:
                assembled_post += "\n \n" + "Ссылка на игру: " + link
        else:
            assembled_post += posttext
            if is_link_allowed:
                assembled_post += "\n \n" + "Ссылка на игру: " + link
            assembled_post += "\n \n" + "Теги: \n" + hashtags

        # Возвращаем ссылку, период публикации, собранный пост и данные о картинке
        return ad_group[1], ad_group[4], assembled_post, image_bytes

if __name__=="__main__":
    ad = Ad("user_ad_groups.db3")


