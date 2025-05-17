# Chat WebSocket API Documentation (for Frontend - Next.js)

This document outlines how to connect to and interact with the real-time chat WebSocket endpoints.

## 1. Base WebSocket URL

The base URL for WebSocket connections will depend on your environment:

* **Development (local):** `ws://localhost:8000/ws/chat/`
* **Staging/Production:** `wss://qader.vip/ws/chat/` (Note `wss` for secure connections)

Make sure to use the correct protocol (`ws` for unencrypted, `wss` for encrypted) and domain.

## 2. Authentication

WebSocket connections are authenticated using the **existing Django session cookie**. This means the user must be logged into the web application (and have a valid session cookie set in their browser) before attempting to establish a WebSocket connection.

The `AuthMiddlewareStack` on the backend handles verifying this session. If the user is not authenticated, the WebSocket connection will be rejected.

## 3. Endpoints and Connection Paths

There are two main WebSocket paths, depending on the user's role:

### 3.1. Student: Connecting to their Mentor Conversation

* **Path:** `/my-conversation/`
* **Full WebSocket URL (Example):** `ws://localhost:8000/ws/chat/my-conversation/`
* **Purpose:** For an authenticated **student** to connect to their active chat conversation with their assigned mentor.
* **Behavior:**
  * The backend will automatically identify the student's assigned mentor.
  * If a conversation already exists, the student will join it.
  * If no conversation exists but a mentor is assigned, a new conversation will be created, and the student will join it.
  * If the student has no mentor assigned, the connection will likely be rejected or fail to establish a specific chat room.

### 3.2. Teacher/Trainer: Connecting to a Specific Student Conversation

* **Path:** `/conversations/<conversation_id>/`
* **Full WebSocket URL (Example for conversation ID 123):** `ws://localhost:8000/ws/chat/conversations/123/`
* **Purpose:** For an authenticated **teacher or trainer** to connect to a specific conversation they have with one of their students.
* **`<conversation_id>`:** This is the unique ID of the conversation. Teachers will typically get this ID from a list of their conversations (e.g., retrieved via the REST API endpoint `GET /api/v1/chat/teacher/conversations/`).
* **Behavior:**
  * The backend will verify that the authenticated teacher is indeed a participant (the teacher) in the specified `conversation_id`.
  * If not authorized or the conversation doesn't exist, the connection will be rejected.

## 4. WebSocket Message Protocol (JSON)

All messages exchanged over the WebSocket are in JSON format.

### 4.1. Client Sending a Message

To send a chat message to the current conversation:

* **Format:**

    ```json
    {
      "message": "Your chat message content here"
    }
    ```

* **Example (JavaScript):**

    ```javascript
    // Assuming 'socket' is an established WebSocket connection
    const messageContent = "Hello, how are you today?";
    socket.send(JSON.stringify({ message: messageContent }));
    ```

### 4.2. Server Sending Messages to Client

The server will send messages to the client for various events. Each message will have a `type` field to indicate its purpose.

#### A. Connection Established (Acknowledgement)

Immediately after a successful connection and joining a chat room, the server sends an acknowledgment.

* **`type`:** `"connection_established"`
* **Payload:**

    ```json
    {
      "type": "connection_established",
      "conversation_id": "string_representation_of_conversation_id", // e.g., "123"
      "room_group_name": "string_internal_group_name" // e.g., "chat_123" (mainly for debugging/info)
    }
    ```

* **Purpose:** Confirms the client is connected to the specified (or determined) conversation. You should typically wait for this before enabling the message input field for the user.

#### B. New Chat Message

When a new chat message is sent by either participant in the conversation.

* **`type`:** `"new_message"`
* **Payload:**

    ```json
    {
      "type": "new_message",
      "message": {
        "id": 101, // Unique ID of the message
        "sender": 5, // User ID (PK) of the sender
        "sender_profile": { // Basic profile info of the sender
          "user_id": 25, // UserProfile ID (PK) of the sender
          "full_name": "John Doe",
          "username": "johndoe",
          "email": "john.doe@example.com",
          "role": "STUDENT" // or "TEACHER", "TRAINER"
        },
        "content": "The actual chat message text.",
        "timestamp": "2023-10-27T10:30:00Z", // ISO 8601 timestamp
        "is_read": false, // Will be true if the recipient has already read it (e.g., on loading history)
                         // For live messages, the recipient client might update this locally or send a "read" event.
        "is_own_message": true // boolean: true if this message was sent by the current client, false otherwise.
                               // This is determined by the server for each connected client.
      }
    }
    ```

* **Purpose:** To display a new chat message in the UI. Use `message.is_own_message` to style messages differently (e.g., align right for own, left for others).

#### C. Error Message (Generic)

If the client sends an invalid message or an error occurs on the server while processing a client's WebSocket message.

* **`type`:** (May not always be present, or could be a generic error type)
* **Payload (Example):**

    ```json
    {
      "error": "Message content cannot be empty."
    }
    ```

    ```json
    {
      "error": "Conversation not established."
    }
    ```

* **Purpose:** To inform the client of an issue. Display appropriately to the user or log for debugging.

## 5. Handling Connections in Next.js (Example Snippet)

This is a conceptual example. You'll integrate this into your React components and state management (e.g., Context API, Zustand, Redux).

```javascript
// Example in a Next.js component (e.g., components/ChatInterface.js)
import React, { useState, useEffect, useRef, useCallback } from 'react';

const ChatInterface = ({ wsPath, conversationIdForDisplay }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  const connectWebSocket = useCallback(() => {
    // Construct the full WebSocket URL
    const protocol = window.location.protocol === 'https лидер:' ? 'wss:' : 'ws:';
    const host = window.location.host; // Or your specific API host
    const fullWsUrl = `${protocol}//${host}/ws/chat${wsPath}`; // wsPath is e.g., "/my-conversation/"

    console.log('Attempting to connect to:', fullWsUrl);
    socketRef.current = new WebSocket(fullWsUrl);

    socketRef.current.onopen = () => {
      console.log('WebSocket connection opened');
      // setIsConnected(true); // Wait for 'connection_established' message
    };

    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received message:', data);

      if (data.type === 'connection_established') {
        setIsConnected(true);
        console.log('Connection established for conversation:', data.conversation_id);
        // You might want to fetch historical messages via REST API here if not already loaded
      } else if (data.type === 'new_message') {
        setMessages((prevMessages) => [...prevMessages, data.message]);
        // If !data.message.is_own_message, you might want to trigger a "mark as read"
        // action via REST API or a WebSocket message if implemented.
      } else if (data.error) {
        console.error('WebSocket server error:', data.error);
        // Handle error display
      }
    };

    socketRef.current.onclose = (event) => {
      console.log('WebSocket connection closed:', event.code, event.reason);
      setIsConnected(false);
      // Implement reconnection logic if desired
    };

    socketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      // Handle error display or reconnection
    };
  }, [wsPath]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (socketRef.current) {
        console.log('Closing WebSocket connection');
        socketRef.current.close();
      }
    };
  }, [connectWebSocket]); // Reconnect if wsPath changes

  const handleSendMessage = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && inputValue.trim()) {
      socketRef.current.send(JSON.stringify({ message: inputValue }));
      setInputValue('');
    }
  };

  return (
    <div>
      {/* Display conversationIdForDisplay or other info */}
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <div className="message-list">
        {messages.map((msg) => (
          <div key={msg.id} className={msg.is_own_message ? 'my-message' : 'other-message'}>
            <strong>{msg.sender_profile?.username || 'System'}: </strong>
            {msg.content}
            <span className="timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
        disabled={!isConnected}
      />
      <button onClick={handleSendMessage} disabled={!isConnected}>Send</button>
    </div>
  );
};

export default ChatInterface;

// How to use it:
// For Student: <ChatInterface wsPath="/my-conversation/" />
// For Teacher: <ChatInterface wsPath={`/conversations/${currentConversationId}/`} conversationIdForDisplay={currentConversationId} />
```

## 6. Important Considerations

* **Error Handling:** Implement robust error handling for connection failures, disconnections, and server-sent error messages.
* **Reconnection Logic:** Consider implementing automatic reconnection attempts if the WebSocket connection drops.
* **Message History:** WebSocket is for real-time. Load historical messages via the REST API (`GET /api/v1/chat/.../messages/`) when a chat interface is opened or when the "connection_established" message is received.
* **Marking Messages as Read:**
  * The backend automatically marks messages as read for a user when they connect to a conversation OR when they fetch messages via the REST API.
  * For real-time "seen" status updates *while both users are connected and active*, you might need to:
        1. Have the client send a specific WebSocket message (e.g., `{"type": "mark_read", "message_id": "..."}`) when they view new messages.
        2. The server would then process this, update the `is_read` status, and potentially broadcast an "update_message_status" event to other participants if needed. This is more advanced.
* **UI State Management:** Manage connection state, messages, and user input effectively within your Next.js application's state.
* **Security:** Always use `wss://` in production. The backend's `AllowedHostsOriginValidator` provides basic protection, but ensure your overall application security is sound.
