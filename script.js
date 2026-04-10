function showloginWindow() {
    let divlogin = document.getElementById("loginWindow");
    divlogin.style.display = "block";
    let divregister = document.getElementById("registerWindow");
    divregister.style.display = "none";
}

function showregisterWindow() {
    let divlogin = document.getElementById("loginWindow");
    divlogin.style.display = "none";
    let divregister = document.getElementById("registerWindow");
    divregister.style.display = "block";
}

function getLoginInfos() {
    let name = document.getElementById("loginusername").value;
    let password = document.getElementById("loginpassword").value;

    return { name, password };
}

function getRegisterInfos() {
    let name = document.getElementById("registerusername").value;
    let password = document.getElementById("registerpassword").value;

    return { name, password };
}

function showMessage(message) {
    const boxes = document.getElementsByClassName("messagebox");
    for (let box of boxes) {
            box.textContent = message;
    }
    setTimeout(() => {
        for (let box of boxes) {
            box.textContent = "";
        }
    }, 2000);
    return
}

function hideLoginRegister() {
    let divlogin = document.getElementById("loginWindow");
    let divregister = document.getElementById("registerWindow");
    divlogin.style.display = "none";
    divregister.style.display = "none";
}

function clearTaskInputs() {
    document.getElementById("new_task_text").value = "";
    document.getElementById("new_task_deadline").value = "";
    document.getElementById("new_task_category").value = "";
}

let apiKey = null;
let userid = null;
let currentTodoId = null;

// POST login
function loginUser() {
    const data = getLoginInfos()

    fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);

        if (result.api_key) {
            apiKey = result.api_key;
            userid = result.userid;
            hideLoginRegister()
            show_dashboard()
        } else {
            showMessage(result.message)
        }
    });
}

// POST register
function registerUser() {
    const data = getRegisterInfos()

    fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);

        if (result.api_key) {
            apiKey = result.api_key;
            userid = result.userid;
            hideLoginRegister()
            show_dashboard()
        } else {
            showMessage(result.message)
        }
    });
}

// GET /user/ID=x/todo
async function getTodos() {
    try {
        const response = await fetch("http://127.0.0.1:5000/user/" + userid + "/todo", {
            method: "GET",
            headers: { "X-API-Key": apiKey }
        });

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Fehler:", error);
        return [];
    }
}

async function show_dashboard() {
    const container = document.getElementById("todo-container");
    container.innerHTML = "";

    const new_list_button = document.createElement("button");
    new_list_button.id = "new_list_btn"
    new_list_button.textContent = "Neue Liste erstellen"
    new_list_button.addEventListener("click", () => {
        create_new_list()
    })
    container.appendChild(new_list_button)

    const todos = await getTodos();

    if (todos != null) {
        todos.forEach(list => {
            const wrapper = document.createElement("div");

            const box = document.createElement("button");
            box.className = "todo-box";
            box.textContent = list.title;

            box.addEventListener("click", () => {
                openTodo(list.todoid);
            });

            const delBtn = document.createElement("button");
            delBtn.textContent = "❌";
            delBtn.style.marginLeft = "10px";

            delBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteList(list.todoid);
            });

            wrapper.appendChild(box);
            wrapper.appendChild(delBtn);
            wrapper.className = "wrapper";

            container.appendChild(wrapper);
        });
    }
}

function showTodoDetail(list) {
    currentTodoId = list.todoid;

    document.getElementById("todo-container").style.display = "none";
    document.getElementById("todo-detail").style.display = "block";

    document.getElementById("detail-title").textContent = list.title;

    const ul = document.getElementById("detail-list");
    ul.innerHTML = "";

    list.todolist.forEach(item => {
        const li = document.createElement("li");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = item.done;

        checkbox.addEventListener("change", () => {
            toggleDone(item.id);
        });

        const text = document.createElement("span");
        text.textContent = `${item.text} | ${item.category} | ${item.deadline}`;

        const del = document.createElement("button");
        del.textContent = "❌";

        del.addEventListener("click", () => {
            deleteTask(item.id);
        });

        li.appendChild(checkbox);
        li.appendChild(text);
        li.appendChild(del);

        ul.appendChild(li);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("back-btn").addEventListener("click", () => {
        document.getElementById("todo-detail").style.display = "none";
        document.getElementById("todo-container").style.display = "block";
        clearTaskInputs();
    });
});

function create_new_list() {
    document.getElementById("todo-container").style.display = "none";
    document.getElementById("new_list").style.display = "block";
}

async function createList() {
    const title = document.getElementById("new_list_title").value;

    if (!title) {
        showMessage("Bitte Titel eingeben");
        return;
    }

    const response = await fetch("http://127.0.0.1:5000/user/" + userid + "/todo", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": apiKey
        },
        body: JSON.stringify({ title: title })
    });

    const result = await response.json();
    showMessage(result.message);

    document.getElementById("new_list").style.display = "none";
    document.getElementById("todo-container").style.display = "block";

    document.getElementById("new_list_title").value = "";

    show_dashboard();
}

function backToDashboard() {
    document.getElementById("new_list").style.display = "none"
    document.getElementById("todo-container").style.display = "block"
}

async function deleteList(todoid) {
    const response = await fetch("http://127.0.0.1:5000/user/" + userid + "/todo", {
        method: "DELETE",
        headers: {
            "X-API-Key": apiKey,
            "todoid": todoid
        }
    });

    const result = await response.json();
    showMessage(result.message);

    show_dashboard();
}

async function addTask() {
    const text = document.getElementById("new_task_text").value;
    const category = document.getElementById("new_task_category").value;
    const deadline = document.getElementById("new_task_deadline").value;

    const response = await fetch("http://127.0.0.1:5000/user/" + userid + "/todo/" + currentTodoId + "/item", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": apiKey
        },
        body: JSON.stringify({ text, category, deadline })
    });

    const result = await response.json();
    showMessage(result.message);

    clearTaskInputs();
    reloadCurrentTodo();
}

async function deleteTask(itemid) {
    await fetch("http://127.0.0.1:5000/user/" + userid + "/todo/" + currentTodoId + "/item", {
        method: "DELETE",
        headers: {
            "X-API-Key": apiKey,
            "itemid": itemid
        }
    });

    reloadCurrentTodo();
}

async function toggleDone(itemid) {
    await fetch(`http://127.0.0.1:5000/user/${userid}/todo/${currentTodoId}/item/${itemid}`, {
        method: "PUT",
        headers: {
            "X-API-Key": apiKey
        }
    });

    reloadCurrentTodo();
}

async function reloadCurrentTodo() {
    const todos = await getTodos();
    const list = todos.find(t => t.todoid === currentTodoId);

    if (!list) {
        show_dashboard();
        return;
    }

    showTodoDetail(list);
}

async function openTodo(todoid) {
    const todos = await getTodos();
    const list = todos.find(t => t.todoid === todoid);
    showTodoDetail(list);
}

