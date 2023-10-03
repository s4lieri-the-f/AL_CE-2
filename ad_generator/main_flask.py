import base64

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib

import ad_generator

app = Flask(__name__)
ad = ad_generator.Ad("user_ad_groups.db3")
SECRET_KEY = "al_ce-2_soya"
app.secret_key = base64.b64encode(hashlib.sha256((SECRET_KEY).encode()).digest()).decode()

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == 'POST':
        user_key = request.form['access_code']
        user_id = ad.validate_key(user_key)  # Assume ad is an instance of your Ad class
        if user_id == None:
            error = 'Неправильный код доступа!'
        elif user_id == -1:
            session['user_id'] = user_id
            return redirect(url_for('admin_dashboard'))
        elif user_id > -1:
            session['user_id'] = user_id
            return redirect(url_for('dashboard'))

    return render_template("index.html", error=error)

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    print(user_id)
    user_group_link = ad.get_user_group_link(ad.get_user_group_id(user_id))

    ad_posts = []
    for post in ad.get_user_group_and_posts(ad.get_user_group_id(user_id)):
        post_id = post[0]  # или каким бы ни был ваш идентификатор поста
        images = ad.get_post_images(post_id)
        encoded_images = [(image[0], "data:image/jpeg;base64," + base64.b64encode(image[1]).decode('utf-8')) for image in images]
        associated_image_ids = [image[0] for image in images]
        ad_posts.append((post, encoded_images))

    all_group_images = [(image[0], "data:image/jpeg;base64," + base64.b64encode(image[1]).decode('utf-8'))
                        for image in ad.get_group_images(ad.get_user_group_id(user_id))]

    ad_groups = ad.get_user_group_and_ad_groups(ad.get_user_group_id(user_id))
    user_group_hashtags = ad.get_user_group_and_hashtags(ad.get_user_group_id(user_id))[0][0]
    available_ad_groups = ad.get_all_ad_groups()
    if user_id<0:
        return redirect(url_for('index'))


    return render_template('dashboard.html',user_group_hashtags=user_group_hashtags,
                           user_group_link=user_group_link,
                           ad_posts=ad_posts,
                           ad_groups=ad_groups,
                           available_ad_groups=available_ad_groups,
                           group_images=all_group_images,
                           associated_image_ids=associated_image_ids)

@app.route('/associate_ad_group', methods=['POST'])
def associate_ad_group():
    data = request.get_json()  # Получаем JSON данные из запроса
    ad_group_id = data.get('adGroupId')
    user_group_id = ad.get_user_group_id(data.get('userId'))

    # Выполняем вашу функцию для ассоциации Ad Group здесь
    success = ad.associate_ad_group_db(ad_group_id, user_group_id)

    # Отправляем ответ обратно на клиент
    return jsonify(success=success)


@app.route('/delete_association', methods=['POST'])
def delete_association():
    data = request.get_json()
    group_id = data.get('groupId')
    user_group_id = ad.get_user_group_id(data.get('userId'))

    # Выполните вашу функцию для удаления ассоциации здесь
    success = ad.delete_association_db(group_id, user_group_id)

    # Отправляем ответ обратно на клиент
    return jsonify(success=success)


@app.route('/get_post_by_id', methods=['POST'])
def get_post_by_id():
    data = request.get_json()  # Получаем JSON данные из запроса
    post_id = data.get('postId')

    # Получаем данные поста из вашей функции
    post_content = ad.get_post_by_id(post_id)

    # Отправляем данные поста обратно на клиент
    return jsonify(postContent=post_content)


@app.route('/submit_edit', methods=['POST'])
def submit_edit():
    selected_images = request.form.getlist('image')
    post_id = request.form.get('postId')
    post_content = request.form.get('postContent')

    ad.delete_all_syncs_for_post(post_id)
    for i in selected_images:
        success = ad.add_post_image_sync(post_id, i)
    ad.update_post(post_id, post_content)

    return jsonify(success=success)

@app.route('/admin')
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    return render_template('admin_dashboard.html')


@app.route("/keys", methods=["GET", "POST"])
def key_validator():
    message = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "validate":
            key = request.form.get("key")
            if ad.validate_key(key):
                message = f"Key is valid! ID: {ad.validate_key(key)}"
            else:
                message = "Key is invalid!"
        elif action == "generate":
            key = request.form.get("key")
            message = f"New key generated: {generate_key(key, SECRET_KEY)}"

    return render_template("keys.html", message=message)


def generate_key(some_string, secret_key, length=12):
    sha_signature = hashlib.sha256((some_string + secret_key).encode()).digest()
    b64_signature = base64.b64encode(sha_signature).decode()
    return b64_signature[:length]


if __name__ == "__main__":
    app.run(host="0.0.0.0")
