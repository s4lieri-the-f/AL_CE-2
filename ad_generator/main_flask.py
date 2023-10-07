import base64

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import hashlib
import asyncio
import requests
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
        user_id = ad.validate_key(user_key)
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
    data = ad.get_user_group_and_posts(ad.get_user_group_id(user_id))
    if len(data) > 0:
        for post in data:
            post_id = post[0]
            images = ad.get_post_images(post_id)
            encoded_images = [(image[0], "data:image/jpeg;base64," + base64.b64encode(image[1]).decode('utf-8')) for
                              image in images]
            associated_image_ids = [image[0] for image in images]

            ad_posts.append((post, encoded_images))
    else:
        encoded_images = [(None, None)]
        associated_image_ids = [None]
        ad_posts.append((None, encoded_images))

    all_group_images = [(image[0], "data:image/jpeg;base64," + base64.b64encode(image[1]).decode('utf-8'))
                        for image in ad.get_group_images(ad.get_user_group_id(user_id))]

    ad_groups = ad.get_user_group_and_ad_groups(ad.get_user_group_id(user_id))
    user_group_hashtags = ad.get_user_group_and_hashtags(ad.get_user_group_id(user_id))[0][0]
    available_ad_groups = ad.get_all_ad_groups()
    user_conf_id = ad.get_user_chat_id(user_id)
    user_account = get_user_account()
    user_account_data = f"{user_account[0]} {user_account[1]}"
    if user_id < 0:
        return redirect(url_for('index'))

    return render_template('dashboard.html', user_group_hashtags=user_group_hashtags,
                           user_group_link=user_group_link,
                           ad_posts=ad_posts,
                           ad_groups=ad_groups,
                           available_ad_groups=available_ad_groups,
                           group_images=all_group_images,
                           associated_image_ids=associated_image_ids,
                           user_conf_id=user_conf_id,
                           user_account_data=user_account_data)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return redirect(request.url)

    file = request.files['image']

    if file.filename == '':
        return redirect(request.url)

    if file and file.filename.endswith(('.png', '.jpg', '.jpeg')):

        image_data = file.read()

        ad.add_post_image_from_bytes(ad.get_user_group_id(session.get('user_id')), image_data)

        return redirect(url_for('dashboard'))

    else:
        return redirect(request.url)


@app.route('/associate_ad_group', methods=['POST'])
def associate_ad_group():
    data = request.get_json()  # Получаем JSON данные из запроса
    ad_group_id = data.get('adGroupId')
    user_group_id = ad.get_user_group_id(data.get('userId'))

    success = ad.associate_ad_group_db(ad_group_id, user_group_id)

    return jsonify(success=success)


@app.route('/add_ad_group', methods=['POST'])
def add_ad_group():
    data = request.get_json()  # Получаем JSON данные из запроса
    ad_group_link = data.get('adGroupLink')
    adGroupHashtags = data.get('adGroupHashtags')
    adGroupPostfix = data.get('adGroupPostfix')
    isAllowed = data.get('linkAllowed')
    adGroupPeriod = data.get('adGroupPeriod')
    user_group_id = ad.get_user_group_id(data.get('userId'))
    row_type = data.get("direction")

    success = ad.add_ad_group(ad_group_link, adGroupHashtags, adGroupPostfix, isAllowed, adGroupPeriod, row_type)

    return jsonify(success=success)


@app.route('/delete_association', methods=['POST'])
def delete_association():
    data = request.get_json()
    group_id = data.get('groupId')
    user_group_id = ad.get_user_group_id(data.get('userId'))

    success = ad.delete_association_db(group_id, user_group_id)

    return jsonify(success=success)


@app.route('/delete_image', methods=['POST'])
def delete_image():
    data = request.get_json()
    image_id = data.get('imageId')
    user_group_id = ad.get_user_group_id(data.get('userId'))

    success = ad.delete_image_db(image_id, user_group_id)

    return jsonify(success=success)


@app.route('/delete_post', methods=['POST'])
def delete_post():
    data = request.get_json()
    post_id = data.get('postId')
    ad.delete_all_syncs_for_post(post_id)
    success = ad.delete_post(post_id)

    # Отправляем ответ обратно на клиент
    return jsonify(success=success)


@app.route('/get_post_by_id', methods=['POST'])
def get_post_by_id():
    data = request.get_json()
    post_id = data.get('postId')

    post_content = ad.get_post_by_id(post_id)

    return jsonify(postContent=post_content)


@app.route('/save_hashtags', methods=['POST'])
def save_hashtags():
    data = request.get_json()
    hashtags = data.get('hashtags')

    ad.update_user_group_hashtags(ad.get_user_group_id(session.get("user_id")), hashtags)

    return jsonify(success=True)

@app.route('/save_conf_id', methods=['POST'])
def save_conf_id():
    data = request.get_json()
    id = data.get('id')

    ad.update_user_conf(session.get("user_id"), id)

    return jsonify(success=True)


@app.route('/submit_edit', methods=['POST'])
def submit_edit():
    selected_images = request.form.getlist('image')
    post_id = request.form.get('postId')
    post_content = request.form.get('postContent')

    ad.delete_all_syncs_for_post(post_id)
    for i in selected_images:
        ad.add_post_image_sync(post_id, i)
    ad.update_post(post_id, post_content)
    success = True
    return jsonify(success=success)


@app.route('/submit_new', methods=['POST'])
def submit_new():
    print("Начинаю добавление!")
    selected_images = request.form.getlist('image')
    post_content = request.form.get('postContent')
    user_group = ad.get_user_group_id(session.get('user_id'))
    post_id = ad.add_post(user_group, post_content)
    print(post_id, user_group, selected_images, post_content)
    for i in selected_images:
        success = ad.add_post_image_sync(post_id, i)

    return jsonify(success=success)


@app.route('/admin')
def admin_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    return render_template('admin_dashboard.html')

@app.route("/user_setup", methods=['POST', 'GET'])
def user_setup():
    return render_template("user_setup.html")
@app.route('/submit_user_data', methods=['POST'])
def submit_user_data():
    data = request.get_json()
    url = data.get('url')
    word = data.get('word')
    admin_code = data.get('adminCode')
    print(admin_code)
    # Check if the admin code is correct
    if admin_code != ad.get_user_access_code(-1):
        return jsonify(message='Invalid Admin Code'), 401

    group = ad.add_user_group(url)
    key = generate_key(word, SECRET_KEY)
    ad.create_user(key, group)

    return jsonify(message=f'Юзер создан! Код доступа: {key}')


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

@app.route("/login_vk", methods=["POST"])
def login_vk():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify(success=False, error="Invalid JSON"), 400
    login = data.get("username")
    password = data.get("password")
    try:
        twofa = data.get("authCode")
        validation_sid = data.get("sid")
    except:
        twofa = None
        validation_sid = None
    token = login_to_vk(login,password, twofa, validation_sid)
    if token[0] == "need_validation":
        if not twofa:
            return jsonify(success=True, requires_2fa=True, sid=token[1])
    elif "error" in token:
        return jsonify(success=False)
    else:
        ad.update_user(session.get("user_id"), login, password, token)
        return jsonify(success=True)

def get_user_account():
    access_token = ad.get_user_token(session.get("user_id"))
    if access_token:
        response = requests.get(
            'https://api.vk.com/method/users.get',
            params={
                'access_token': access_token,
                'v': "5.131"
            }
        )
        data = response.json()
        if 'response' in data:
            user = data['response'][0]
            first_name = user['first_name']
            last_name = user['last_name']
            return [first_name, last_name]
        else:
            print("Error:", data['error']['error_msg'])
    else:
        return ["Не", " авторизовано!"]


def generate_key(some_string, secret_key, length=12):
    sha_signature = hashlib.sha256((some_string + secret_key).encode()).digest()
    b64_signature = base64.b64encode(sha_signature).decode()
    return b64_signature[:length]

def login_to_vk(login, password, twofa, validation_sid):
    if not twofa:
        response = requests.get(
            "https://oauth.vk.com/token?grant_type=password",
            params={
                "grant_type": "password",
                "client_id": 2274003,
                "client_secret": "hHbZxrka2uZ6jB1inYsH",
                "username": login,
                "password": password,
                "v": "5.131",
            },
        )
    else:
        params = {
            "grant_type": "password",
            "client_id": 2274003,
            "client_secret": "hHbZxrka2uZ6jB1inYsH",
            "username": login,
            "password": password,
            "code": twofa,
            "validation_sid": validation_sid,
            "v": "5.131"
        }

        response = requests.get("https://oauth.vk.com/token?grant_type=password", params=params)
    token_data = response.json()
    if token_data.get('error') == 'need_validation':
        validation_sid = token_data['validation_sid']
        return "need_validation", validation_sid
    elif token_data.get("error"):
        return f"error: {token_data.get('error')}"
    return token_data.get("access_token", "")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
