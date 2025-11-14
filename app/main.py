from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.routers import bookmarks

app = FastAPI(title="KeepShot MVP")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(bookmarks.router, prefix="/api")

# Connected clients
clients = []

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Server received: {data}")
    except:
        clients.remove(websocket)

# Function to push notifications to all clients
async def push_notification(message: str):
    for client in clients:
        await client.send_text(message)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KeepShot Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="max-w-2xl mx-auto mt-10">
            <h1 class="text-3xl font-bold mb-5">KeepShot Dashboard</h1>
            <ul id="notifications" class="space-y-2"></ul>
        </div>

        <script>
            const ws = new WebSocket("ws://localhost:8000/ws/notifications");
            ws.onmessage = function(event) {
                const notifList = document.getElementById("notifications");
                const li = document.createElement("li");
                li.textContent = event.data;
                li.className = "bg-white p-3 rounded shadow";
                notifList.prepend(li);
            };
        </script>
    </body>
    </html>
    """
    return html_content