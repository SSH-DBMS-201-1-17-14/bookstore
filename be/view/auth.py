from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import user

bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


@bp_auth.route("/login", methods=["POST"])
def login():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    terminal = request.json.get("terminal", "")
    u = user.User()
    code, message, token = u.login(user_id=user_id, password=password, terminal=terminal)
    return jsonify({"message": message, "token": token}), code


@bp_auth.route("/logout", methods=["POST"])
def logout():
    user_id: str = request.json.get("user_id")
    token: str = request.headers.get("token")
    u = user.User()
    code, message = u.logout(user_id=user_id, token=token)
    return jsonify({"message": message}), code


@bp_auth.route("/register", methods=["POST"])
def register():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    u = user.User()
    code, message = u.register(user_id=user_id, password=password)
    return jsonify({"message": message}), code


@bp_auth.route("/unregister", methods=["POST"])
def unregister():
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    u = user.User()
    code, message = u.unregister(user_id=user_id, password=password)
    return jsonify({"message": message}), code


@bp_auth.route("/password", methods=["POST"])
def change_password():
    user_id = request.json.get("user_id", "")
    old_password = request.json.get("oldPassword", "")
    new_password = request.json.get("newPassword", "")
    u = user.User()
    code, message = u.change_password(user_id=user_id, old_password=old_password, new_password=new_password)
    return jsonify({"message": message}), code

@bp_auth.route("/store_search_title", methods=["POST"])
def store_search_title():
    user_id = request.json.get("user_id","")
    store_id = request.json.get("store_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message, book_id= u.store_search_title(user_id=user_id, store_id = store_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/store_search_book_intro", methods=["POST"])
def store_search_book_intro():
    user_id = request.json.get("user_id","")
    store_id = request.json.get("store_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message, book_id = u.store_search_book_intro(user_id=user_id, store_id = store_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/store_search_content", methods=["POST"])
def store_search_content():
    user_id = request.json.get("user_id","")
    store_id = request.json.get("store_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message, book_id = u.store_search_content(user_id=user_id, store_id = store_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/global_search_title", methods=["POST"])
def global_search_title():
    user_id = request.json.get("user_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message , book_id = u.global_search_title(user_id=user_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/global_search_book_intro", methods=["POST"])
def global_search_book_intro():
    user_id = request.json.get("user_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message, book_id = u.global_search_book_intro(user_id=user_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/global_search_content", methods=["POST"])
def global_search_content():
    user_id = request.json.get("user_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message, book_id = u.global_search_content(user_id=user_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/global_search_tag", methods=["POST"])
def global_search_tag():
    user_id = request.json.get("user_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    u = user.User()
    code, message, book_id = u.global_search_tag(user_id=user_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code


@bp_auth.route("/store_search_tag", methods=["POST"])
def store_search_tag():
    user_id = request.json.get("user_id","")
    search_info = request.json.get("search_info","")
    page = request.json.get("page","")
    store_id=request.json.get("store_id","")
    u = user.User()
    code, message, book_id = u.store_search_tag(user_id=user_id,store_id=store_id,search_info = search_info,page = page)
    return jsonify({"message": message,"book_id":book_id}), code

@bp_auth.route("/get_store_id", methods=["POST"])
def get_store_id():
    user_id = request.json.get("user_id","")
    book_id = request.json.get("book_id","")
    u = user.User()
    code,  message, store_id_list = u.get_store_id(user_id=user_id,book_id = book_id)
    return jsonify({"message": message,"store_id_list": store_id_list}), code
