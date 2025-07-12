import uuid


class Room_Manager:
    """
    Manages the creation, joining, and leaving of chat rooms.
    Each room is identified by a unique ID and stores a list of member names.
    """

    def __init__(self):
        self.rooms = {}  # Stores room_id: [member_name1, member_name2, ...]

    def create_room(self, host_name: str) -> str:
        """
        Creates a new room with a unique ID and adds the host as the first member.
        """
        room_id = str(uuid.uuid4())[:8]
        self.rooms[room_id] = [host_name]  # Initialize with a list of members
        return room_id

    def room_exists(self, room_id: str) -> bool:
        """
        Checks if a room with the given ID exists.
        """
        return room_id in self.rooms

    def join_room(self, room_id: str, u_name: str) -> bool:
        """
        Adds a user to an existing room.
        Returns True if the user successfully joined or was already in the room, False otherwise.
        """
        if room_id not in self.rooms:
            return False  # Room does not exist

        if u_name in self.rooms[room_id]:
            return True  # User is already in the room, consider it a successful 'join'

        self.rooms[room_id].append(u_name)
        return True

    def leave_room(self, room_id: str, u_name: str) -> bool:
        """
        Removes a user from a room. If the room becomes empty after the user leaves,
        the room is also removed from the manager.
        """
        if room_id not in self.rooms:
            return False  # Room does not exist

        if u_name in self.rooms[room_id]:
            self.rooms[room_id].remove(u_name)
            # If the room becomes empty after the user leaves, remove the room itself
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            return True
        return False

    def get_users(self, room_id: str) -> list:
        """
        Retrieves the list of users currently in a specified room.
        """
        return self.rooms.get(room_id, [])
