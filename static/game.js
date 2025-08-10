var socket = io();

var hasJoined = false;

socket.on('connect', function() {});

function joinRoom() {
    socket.emit("join_game", {"username": document.getElementById("username-input").value})
}

const error = document.getElementById("error");
function showError(text) {
    error.innerText = text;
    error.className = "visible";
    setTimeout(() => {error.className = "";}, 2500);
}

function setView(viewId) {
    document.querySelectorAll(".single-view").forEach((value, index, array) => {
        if (value.id == viewId) {
            value.classList.add("visible");
        } else {
            value.classList.remove("visible");
        }
    });
}

function readyUp() {
    socket.emit("ready_up");
}
function submitArticleGuess() {
    socket.emit("article_guess", {"guess": document.getElementById("article-guess").value})
}

socket.on("player_list", function(data) {
    const players = data["players"];
    const playerList = document.getElementById("player-list");

    playerList.innerHTML = "";

    players.forEach((value, index, array) => {
        const playerElement = document.createElement("div");
        playerElement.innerText = value;
        playerElement.className = "player-name";
        playerList.appendChild(playerElement);
    })
});

socket.on("loading", function(data) {
    if (!hasJoined) return;
    setView("loader");
    document.getElementById("loader").innerText = data["message"];
})

socket.on("join_game_pass", function(data) {
    console.log("pass")
    console.log(data)
    setView("waiting-for-players");
    hasJoined = true;
});
socket.on("join_game_fail", function(data) {
    console.log("fail")
    console.log(data);
    showError(data["error"]);
});

socket.on("ready_up_resp", function(data) {
    if (!hasJoined) return;
    document.querySelectorAll(".ready-button").forEach((value, index, array) => {
        value.innerText = data["is_readied"] ? "Unready" : "Ready Up";
    })
})

socket.on("article", function(data) {
    if (!hasJoined) return;
    setView("guessing");
    console.log(data["text"])
    document.getElementById("article-snippet").innerText = data["page"];
})

socket.on("guess_accepted", function(data) {
    if (!hasJoined) return;
    setView("waiting-for-submit");
})

const scoreboard = document.getElementById("scoreboard");
function makeScore(value, score, delta, guessed) {
    const entry = document.createElement("div");
    entry.className = "scoreboard-entry";
    
    const username = document.createElement("div");
    username.className = "scoreboard-username";
    username.innerText = value;
    scoreboard.appendChild(username);

    const scoreEl = document.createElement("div");
    scoreEl.className = "scoreboard-score";
    scoreEl.innerText = score;
    scoreboard.appendChild(scoreEl);

    const scoreDelta = document.createElement("div");
    scoreDelta.className = "scoreboard-score-delta";
    scoreDelta.innerText = delta;
    scoreboard.appendChild(scoreDelta);

    const guessedEl = document.createElement("div");
    guessedEl.className = "scoreboard-guess";
    guessedEl.innerText = guessed;
    scoreboard.appendChild(guessedEl);

    //.appendChild(entry);
}
socket.on("round_complete", function(data) {
    if (!hasJoined) return;
    const scores = data["scores"];
    setView("results");
    document.getElementById("scoreboard").innerHTML = "";
    document.getElementById("article-title").innerText = "The article was " + data["article"];
    makeScore("Username", "Score", "Change", "Guess");
    Object.keys(scores).forEach((value, index, array) => {
        makeScore(value, scores[value][0], "+" + scores[value][1], scores[value][2]);
    })
})