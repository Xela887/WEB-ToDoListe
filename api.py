from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_cors import cross_origin
import json
import uuid

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Admin-API-Key
ADMIN_API_KEY = "supergeheimer-admin-key-123"


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({"message": "Name oder Passwort fehlt"}), 400

    new_user = save_new_user(name, password)

    return jsonify({
        "message": "Benutzer erfolgreich registriert",
        "userid": new_user["id"],
        "api_key": new_user["api_key"]
    }), 201


@app.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()

    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({"message": "Name oder Passwort fehlt"}), 400

    users = load_user()["user"]

    user = next((u for u in users if u["name"] == name), None)

    if not user:
        return jsonify({"message": "Benutzer existiert nicht"}), 404

    if user["passwort"] != password:
        return jsonify({"message": "Passwort falsch"}), 401

    return jsonify({
        "message": "Login erfolgreich",
        "userid": user["id"],
        "api_key": user["api_key"]
    }), 200


@app.route("/user", methods=["GET", "DELETE"])
def get_user():
    api_key = request.headers.get("Admin-API-Key")

    if not api_key:
        return jsonify({"message": "Admin-API-Key fehlt"}), 401

    if api_key != ADMIN_API_KEY:
        return jsonify({"message": "Keine Berechtigung"}), 403

    if request.method == "GET":
        return jsonify(load_user())
    elif request.method == "DELETE":
        id_to_delete = request.json.get("id")

        if not id_to_delete:
            return jsonify({"message": "Bitte ID zum löschen eingeben"}), 400

        data = load_user()
        users = data["user"]

        user = next((u for u in users if u["id"] == int(id_to_delete)), None)

        if not user:
            return jsonify({"message": "Keinen User mit dieser ID gefunden"}), 400

        users.remove(user)
        save_user(data)

        return jsonify({"message": "User gelöscht"}), 200


@app.route("/user/<int:id>", methods=["GET", "PUT", "DELETE"])
def user_account(id):
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"message": "API-Key fehlt"}), 401

    data = load_user()
    users = data["user"]

    user = next((u for u in users if u["api_key"] == api_key), None)

    if not user:
        return jsonify({"message": "Ungültiger API-Key"}), 403

    if user["id"] != id:
        return jsonify({"message": "Keine Berechtigung für diesen User"}), 403

    if request.method == "GET":
        return jsonify({
            "id": user["id"],
            "name": user["name"]
        }), 200

    if request.method == "PUT":
        new_password = request.json.get("password")

        if not new_password:
            return jsonify({"message": "Neues Passwort fehlt"}), 400

        user["passwort"] = new_password
        save_user(data)

        return jsonify({"message": "Passwort erfolgreich geändert"}), 200

    if request.method == "DELETE":
        users.remove(user)
        save_user(data)

        return jsonify({"message": "Benutzerkonto gelöscht"}), 200


@app.route("/user/<int:id>/todo", methods=["GET", "POST", "DELETE"])
def user_todos(id):
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"message": "API-Key fehlt"}), 401

    data = load_user()
    users = data["user"]

    user = next((u for u in users if u["api_key"] == api_key), None)

    if not user:
        return jsonify({"message": "Ungültiger API-Key"}), 403

    if user["id"] != id:
        return jsonify({"message": "Keine Berechtigung für diesen User"}), 403

    if request.method == "GET":
        todos = get_user_todos(user["id"])
        return jsonify(todos)
    elif request.method == "POST":
        data = request.get_json()
        title = data.get("title")

        if title == "":
            return jsonify({"message": "Bitte Titel der Todo eingeben"}), 400

        save_new_todo(user["id"], title)
        return jsonify({"message": "Todo erstellt"})
    elif request.method == "DELETE":
        todos = get_user_todos(user["id"])
        todoid = request.headers.get("todoid")

        if not todoid:
            return jsonify({"message": "Bitte ID der Todo eingeben"}), 400

        deleted_todo = [t for t in todos if t.get("todoid") == int(todoid)]
        if not deleted_todo:
            return  jsonify({"message": "Keine Todo mit dieser ID"}), 400

        data_todos = load_todos()
        all_todos = data_todos["todos"]

        all_todos = [t for t in all_todos if not (t["userid"] == user["id"] and t["todoid"] == int(todoid))]

        data_todos["todos"] = all_todos
        save_todos(data_todos)

        return jsonify({"message": "Todo gelöscht", "todo": deleted_todo}), 200


@app.route("/user/<int:id>/todo/<int:todoid>", methods=["GET", "PUT"])
def show_user_todo_data(id, todoid):
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"message": "API-Key fehlt"}), 401

    data = load_user()
    users = data["user"]

    user = next((u for u in users if u["api_key"] == api_key), None)

    if not user:
        return jsonify({"message": "Ungültiger API-Key"}), 403

    if user["id"] != id:
        return jsonify({"message": "Keine Berechtigung für diesen User"}), 403

    if request.method == "GET":
        todos = get_user_todos(user["id"])
        todo = [t for t in todos if t.get("todoid") == int(todoid)]

        if not todo:
            return  jsonify({"message": "Keine Todo mit dieser ID"}), 400

        return jsonify(todo)

    elif request.method == "PUT":
        todochanges = request.json.get("todochanges")
        newtitle = request.json.get("newtitle")

        if not newtitle:
            return jsonify({"message": "ToDo-Liste muss einen Titel haben"}), 400

        data_todos = load_todos()
        todos = data_todos["todos"]
        todo = next((t for t in todos if t["userid"] == user["id"] and t["todoid"] == todoid), None)

        if not todo:
            return jsonify({"message": "Keine Todo mit dieser ID"}), 400

        todo["title"] = newtitle
        todo["todolist"] = todochanges

        save_todos(data_todos)
        return jsonify({"message": "ToDo-Änderungen gespeichert"}), 200


@app.route("/user/<int:id>/todo/<int:todoid>/item/<int:itemid>", methods=["PUT"])
def update_item(id, todoid, itemid):
    api_key = request.headers.get("X-API-Key")

    users = load_user()["user"]
    user = next((u for u in users if u["api_key"] == api_key), None)

    if not user or user["id"] != id:
        return jsonify({"message": "Keine Berechtigung"}), 403

    data = load_todos()
    todos = data["todos"]

    todo = next((t for t in todos if t["userid"] == id and t["todoid"] == todoid), None)

    item = next((i for i in todo["todolist"] if i["id"] == itemid), None)

    if not item:
        return jsonify({"message": "Item nicht gefunden"}), 404

    item["done"] = not item["done"]

    save_todos(data)

    return jsonify({"message": "Status geändert"})


@app.route("/user/<int:id>/todo/<int:todoid>/item", methods=["POST", "DELETE"])
@cross_origin()
def manage_todo_items(id, todoid):
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        return jsonify({"message": "API-Key fehlt"}), 401

    users = load_user()["user"]
    user = next((u for u in users if u["api_key"] == api_key), None)

    if not user or user["id"] != id:
        return jsonify({"message": "Keine Berechtigung"}), 403

    data = load_todos()
    todos = data["todos"]

    todo = next((t for t in todos if t["userid"] == id and t["todoid"] == todoid), None)

    if not todo:
        return jsonify({"message": "Todo nicht gefunden"}), 404

    if request.method == "POST":
        new_item = request.get_json()

        if not new_item.get("text"):
            return jsonify({"message": "Text fehlt"}), 400

        new_id = max([i["id"] for i in todo["todolist"]], default=0) + 1

        item = {
            "id": new_id,
            "text": new_item.get("text"),
            "category": new_item.get("category"),
            "deadline": new_item.get("deadline"),
            "done": False
        }

        todo["todolist"].append(item)
        save_todos(data)

        return jsonify({"message": "Aufgabe hinzugefügt"}), 200

    elif request.method == "DELETE":
        item_id = request.headers.get("itemid")

        if not item_id:
            return jsonify({"message": "Item ID fehlt"}), 400

        todo["todolist"] = [i for i in todo["todolist"] if i["id"] != int(item_id)]
        save_todos(data)

        return jsonify({"message": "Aufgabe gelöscht"}), 200




def generate_api_key():
    return str(uuid.uuid4())

def load_user():
    try:
        with open("user.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"user": []}

    return data

def save_new_user(name, password):
    data = load_user()
    users = data["user"]

    new_id = max([u["id"] for u in users], default=0) + 1

    new_user = {
        "id": new_id,
        "name": name,
        "passwort": password,
        "api_key": generate_api_key()
    }

    users.append(new_user)

    try:
        with open("user.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

    return new_user

def save_user(data):
    try:
        with open("user.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

def load_todos():
    try:
        with open("todos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"todos": []}

    return data

def save_new_todo(userid, title):
    data = load_todos()
    todos = data["todos"]

    todoid = get_next_todoid(userid)

    new_todo = {
        "userid": userid,
        "todoid": todoid,
        "title": title,
        "todolist": []
    }

    todos.append(new_todo)

    try:
        with open("todos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")

    return new_todo

def save_todos(data):
    try:
        with open("todos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")


def get_next_todoid(userid):
    data = load_todos()

    user_todos = [t for t in data.get("todos", []) if t.get("userid") == userid]

    if not user_todos:
        return 1

    max_id = max(t.get("todoid", 0) for t in user_todos)

    return max_id + 1

def get_user_todos(userid):
    data = load_todos()

    user_todos = [t for t in data.get("todos", []) if t.get("userid") == userid]

    if not user_todos:
        return []

    return user_todos




if __name__ == "__main__":
    app.run(debug=True)
