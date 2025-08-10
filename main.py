import flask
import dotenv
import os
from flask_socketio import SocketIO
from random import choice
import requests
import wikitextparser as wtp
from fuzzywuzzy import fuzz

print("""db   d8b   db d888888b db   dD d888888b  d888b  db    db d88888b .d8888. .d8888. d8888b. 
88   I8I   88   `88'   88 ,8P'   `88'   88' Y8b 88    88 88'     88'  YP 88'  YP 88  `8D 
88   I8I   88    88    88,8P      88    88      88    88 88ooooo `8bo.   `8bo.   88oobY' 
Y8   I8I   88    88    88`8b      88    88  ooo 88    88 88~~~~~   `Y8b.   `Y8b. 88`8b   
`8b d8'8b d8'   .88.   88 `88.   .88.   88. ~8~ 88b  d88 88.     db   8D db   8D 88 `88. 
 `8b8' `8d8'  Y888888P YP   YD Y888888P  Y888P  ~Y8888P' Y88888P `8888Y' `8888Y' 88   YD 
By Boyne Gregg""")

dotenv.load_dotenv()

print("Debug mode is", os.getenv("DEBUG"))

with open("articles_processed.txt", "r+") as articles:
    article_list = articles.readlines()

app = flask.Flask(__name__)

if os.getenv("DEBUG"):
    app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

socketio = SocketIO(app)

accepting_new_players = True

current_article_title = None

def make_client(name, connection_id):
    return {
        "name": name,
        "connection_id": connection_id,
        "is_ready": False,
        "score": 0,
        "score_delta": 0,
        "last_guessed": None
    }

connected_clients = []

def get_client_name_exists(name):
    for client in connected_clients:
        if client["name"] == name: return True
    return False

def get_client_by_id(sid):
    for i in range(0, len(connected_clients)):
        if connected_clients[i]["connection_id"] == sid:
            return connected_clients[i]
        
def get_all_clients_ready():
    for client in connected_clients:
        if not client["is_ready"]: return False
    return True
def unready_all_players():
    for client in connected_clients:
        client["is_ready"] = False

    socketio.emit("ready_up_resp", {"is_readied": False})

def remove_client_by_id(sid):
    for i in range(0, len(connected_clients)):
        if connected_clients[i]["connection_id"] == sid:
            connected_clients.pop(i)
            return
        
def get_page(name: str):
    name = name.removesuffix("\n")
    response = requests.get("https://api.wikimedia.org/core/v1/wikipedia/en/page/" + name, headers={
        'User-Agent': 'WikiGuessr (boynegregg312@gmail.com)'
    })
    data = response.json()
    if "redirect_target" in data.keys(): return None
    wikicode = wtp.parse(data["source"])
    text = ""
    while len(text) < 50:
        text = choice(wikicode.sections)
        text = text.plain_text()
    return text

def emit_player_list():
    socketio.emit("player_list", {"players": [client["name"] for client in connected_clients]})

def start_round():
    global accepting_new_players, current_article_title
    accepting_new_players = False
    unready_all_players()
    socketio.emit("loading", {"message": "Finding an article..."})
    page = None
    while page == None:
        article = choice(article_list)
        page = get_page(article)

    current_article_title = article
    socketio.emit("article", {"page": page})


@app.route("/favicon.ico")
def favicon():
    return flask.send_file("static/WikiGuessr.ico")

@app.route("/")
def index():
    return flask.render_template("index.html")

@socketio.on("disconnect")
def disconnect(reason):
    global accepting_new_players
    remove_client_by_id(flask.request.sid)
    emit_player_list()
    if len(connected_clients) == 0: accepting_new_players = True
    if len(connected_clients) > 0 and get_all_clients_ready():
        if accepting_new_players:
            start_round()
        else:
            socketio.emit("round_complete", {"scores": {client["name"]: (client["score"], client["score_delta"], client["last_guessed"]) for client in connected_clients}, "article": current_article_title})
            accepting_new_players = True
            unready_all_players()



@socketio.on("join_game")
def join_game(data):
    username = data["username"]
    username = username.strip()
    error = None
    if get_client_name_exists(username):
        error = "The given username is taken"
    elif not accepting_new_players:
        error = "There is already a game going"
    elif len(username) > 12:
        error = "Username must be less than or equal to twelve characters"
    elif len(username) < 3:
        error = "Username must be at least three characters"
    if error is not None:
        socketio.emit("join_game_fail", {"error": error}, to=flask.request.sid)
        return
    connected_clients.append(make_client(username, flask.request.sid))
    socketio.emit("join_game_pass", {}, to=flask.request.sid)
    emit_player_list()

@socketio.on("ready_up")
def ready_up():
    client = get_client_by_id(flask.request.sid)
    if not client: return
    if client["is_ready"]:
        client["is_ready"] = False
        socketio.emit("ready_up_resp", {"is_readied": False}, to=flask.request.sid)
    else:
        client["is_ready"] = True
        socketio.emit("ready_up_resp", {"is_readied": True}, to=flask.request.sid)
    
    if get_all_clients_ready(): # The game can start
        start_round()

@socketio.on("article_guess")
def article_guess(data):
    global accepting_new_players
    if current_article_title == None: return
    guess = data["guess"]
    score = fuzz.ratio(guess, current_article_title)
    client = get_client_by_id(flask.request.sid)
    client["score"] += score
    client["score_delta"] = score
    client["is_ready"] = True
    client["last_guessed"] = guess
    socketio.emit("guess_accepted", to=flask.request.sid)
    if get_all_clients_ready():
        socketio.emit("round_complete", {"scores": {client["name"]: (client["score"], client["score_delta"], client["last_guessed"]) for client in connected_clients}, "article": current_article_title})
        accepting_new_players = True
        unready_all_players()


if __name__ == "__main__":
    if os.getenv("DEBUG") == "True":
        print("Stating server in debug mode (0.0.0.0:8080)")
        socketio.run(app, "0.0.0.0", 8080)
    else:
        print("Starting server in production mode (0.0.0.0:80)")
        socketio.run(app, "0.0.0.0", 80)