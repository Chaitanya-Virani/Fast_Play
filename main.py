from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import random
import string
import uuid  # Import uuid for room_manager

# Import the Room_Manager class from room.py
# IMPORTANT: Adjust this import if your room.py is in a 'backend' subdirectory
# For this code, I'm assuming room.py is in the same directory as main.py
from backend.room import Room_Manager

app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# Configure Jinja2Templates to load templates from the "templates" directory
templates = Jinja2Templates(directory="templates")

# Instantiate the Room_Manager globally to manage all rooms
room_manager = Room_Manager()

# Dictionary to store active WebSocket connections for each room.
# Key: room_id (str), Value: List of WebSocket objects
active_connections = {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Renders the 'join.html' template. This is the entry point for users
    to either join an existing room or create a new one.
    """
    return templates.TemplateResponse("join.html", {"request": request})


@app.get("/join_room", response_class=HTMLResponse)
async def join(request: Request, room_id: str, u_name: str):
    """
    Handles the request to join a specific room.

    Args:
        request: The FastAPI Request object.
        room_id: The ID of the room to join.
        u_name: The username of the person joining.

    Returns:
        An HTMLResponse rendering either 'index.html' (if successful)
        or 'no_room.html'/'join.html' with an error message (if unsuccessful).
    """
    # Check if the room exists using the room_manager
    if not room_manager.room_exists(room_id):
        # If the room does not exist, render 'no_room.html'
        return templates.TemplateResponse("no_room.html", {
            "request": request,
            "room_id": room_id
        })

    # Attempt to join the room using the room_manager.
    # The room_manager's join_room method returns False if the username
    # is already present in the room, implying unique usernames per room.
    if room_manager.join_room(room_id, u_name):
        # If joining is successful, ensure the room_id exists in active_connections
        # and prepare to add the WebSocket connection later.
        if room_id not in active_connections:
            active_connections[room_id] = []

        # Get the host's name from room_manager
        # Assuming the first member in the room_manager's list is the host
        room_members = room_manager.get_users(room_id)
        current_host = room_members[0] if room_members else "Unknown Host"

        # Render the 'index.html' template, which will serve as the chat room interface
        return templates.TemplateResponse("index.html", {
            "request": request,
            "u_name": u_name,
            "room_id": room_id,
            "host_name": current_host  # Pass the host's name to the template
        })
    else:
        # If joining failed (e.g., username already taken in the room),
        # redirect back to the join page with an informative error message.
        return templates.TemplateResponse("join.html", {
            "request": request,
            "error_message": f"Could not join room '{room_id}' with name '{u_name}'. "
                             f"This username might already be in use in this room, or there was another issue."
        })


@app.get("/create_room", response_class=HTMLResponse)
async def create_room(request: Request):
    """
    Handles the request to create a new room.
    Generates a unique room ID using Room_Manager and redirects the host to join it.
    """
    host_name = "Host"  # Default host name for the creator of the room
    # Create a new room using the room_manager, which generates a unique room ID
    room_id = room_manager.create_room(host_name)

    # Redirect the 'Host' to the '/join_room' endpoint for the newly created room.
    # This automatically puts the host into their new room.
    return RedirectResponse(url=f"/join_room?room_id={room_id}&u_name={host_name}")


@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: str):
    """
    Manages WebSocket connections for real-time chat within rooms.
    Accepts connections, adds them to active_connections, and handles message broadcasting.
    """
    await websocket.accept()  # Accept the WebSocket connection

    # Add the new WebSocket connection to the list of active connections for this room
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)

    # Broadcast a message to all clients in the room that a new user has joined
    await broadcast_message(room_id, f"User {client_id} has joined the chat.")

    try:
        while True:
            # Continuously receive messages from the current client
            data = await websocket.receive_text()
            # Broadcast the received message (prefixed with client_id) to all clients in the same room
            await broadcast_message(room_id, f"{client_id}: {data}")
    except WebSocketDisconnect:
        # This block executes when a client disconnects (e.g., closes browser tab)

        # Remove the disconnected WebSocket from the active connections list for its room
        if websocket in active_connections[room_id]:
            active_connections[room_id].remove(websocket)

        # Broadcast a message to the remaining clients that a user has left
        await broadcast_message(room_id, f"User {client_id} has left the chat.")

        # If the room becomes empty after a user leaves, remove it from active_connections.
        # Optionally, you could also remove it from room_manager.rooms if desired for cleanup.
        if not active_connections[room_id]:
            del active_connections[room_id]
            # Optional: Remove the room from room_manager if it's completely empty
            room_manager.leave_room(room_id, client_id)  # Call leave_room to update room_manager's state
            # Note: room_manager.leave_room also handles removing the room if it becomes empty.


async def broadcast_message(room_id: str, message: str):
    """
    Sends a given message to all active WebSocket connections within a specified room.
    """
    # Check if the room has any active connections before attempting to broadcast
    if room_id in active_connections:
        # Iterate over a copy of the list to avoid issues if connections are removed during iteration
        for connection in list(active_connections[room_id]):
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                # Handle cases where a WebSocket might be closed unexpectedly during broadcast
                print(f"Error sending message to a client in room {room_id}: {e}")
                # Optionally remove the problematic connection
                if connection in active_connections[room_id]:
                    active_connections[room_id].remove(connection)
