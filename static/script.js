document.addEventListener("DOMContentLoaded", () => {
  // Get room ID and username from data attributes on the body element
  const roomId = document.body.dataset.room_id;
  const uName = document.body.dataset.u_name;

  // Ensure essential data is available before proceeding
  if (!roomId || !uName) {
    console.error("Room ID or Username not found in data attributes. Cannot establish WebSocket.");
    return;
  }

  // Establish WebSocket connection to the server endpoint
  const socket = new WebSocket(`ws://${window.location.host}/ws/${roomId}/${uName}`);

  // Get UI elements for chat
  const messagesDiv = document.getElementById('messages');
  const messageInput = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  const leaveButton = document.getElementById('leaveButton'); // Get the leave button

  // Event listener for when the WebSocket connection is successfully opened
  socket.onopen = () => {
    console.log("✅ Connected to WebSocket room:", roomId);
    // No initial message sent from client here to avoid duplicates.
    // The server will send a "User joined" message.
  };

  // Event listener for when a message is received from the server via WebSocket
  socket.onmessage = (event) => {
    console.log("📩 Message from server:", event.data);
    // Display the received message in the chat area
    if (messagesDiv) {
      const p = document.createElement('p');
      p.textContent = event.data;
      p.classList.add('text-white', 'mb-1'); // Add some basic styling for messages
      messagesDiv.appendChild(p);
      // Scroll to the bottom of the chat to show the latest message
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  };

  // Event listener for when the WebSocket connection is closed
  socket.onclose = () => {
    console.log("❌ WebSocket disconnected.");
    // You might want to display a message to the user or try to reconnect.
  };

  // Event listener for WebSocket errors
  socket.onerror = (error) => {
    console.error("⚠️ WebSocket error:", error);
  };

  // --- Send Message Functionality ---
  if (sendButton && messageInput) {
    // Send message on button click
    sendButton.addEventListener('click', () => {
      const message = messageInput.value.trim();
      if (message) {
        socket.send(message); // Send the message over the WebSocket
        messageInput.value = ''; // Clear the input field
      }
    });

    // Send message on Enter key press in the input field
    messageInput.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault(); // Prevent default form submission if input is inside a form
        sendButton.click(); // Simulate a click on the send button
      }
    });
  }

  // --- Leave Button Functionality ---
  if (leaveButton) {
    leaveButton.addEventListener('click', () => {
      console.log("Leaving room...");
      socket.close(); // Close the WebSocket connection
      // Redirect to the join page after a short delay to allow WebSocket to close gracefully
      setTimeout(() => {
        window.location.href = '/'; // Redirect to the root URL (join page)
      }, 100); // Small delay
    });
  }
});
