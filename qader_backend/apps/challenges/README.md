## Frontend Integration Guide: Django Channels WebSockets (Next.js)

This guide explains how to connect your Next.js frontend application to the real-time WebSocket endpoints provided by the Django backend for the `challenges` feature. This allows for live updates on challenge invitations, status changes, participant readiness, answers, and results.

### Prerequisites

1. **Backend Running:** The Django development server must be running using `daphne` (e.g., `daphne qader_project.asgi:application`).
2. **Next.js Project:** A working Next.js application setup.
3. **Authentication:** Users must be authenticated via the standard HTTP login flow. The WebSocket connection relies on the Django session cookie set in the browser during login.

### Environment Configuration

It's best practice to configure the base WebSocket URL using environment variables.

1. Create or update your `.env.local` file in the root of your Next.js project:

    ```bash
    # .env.local

    # Ensure this matches the host and port where Daphne is running
    NEXT_PUBLIC_WS_BASE_URL=wss://qader.vip/ws
    ```

2. **Accessing the Variable:** In your Next.js code, you can access this as `process.env.NEXT_PUBLIC_WS_BASE_URL`. The `NEXT_PUBLIC_` prefix makes it available in the browser.

### Core WebSocket Connection Logic (Custom Hook)

Encapsulating WebSocket logic within a custom hook is recommended for reusability and clean component code.

```typescript
// hooks/useWebSocket.ts
import { useState, useEffect, useRef, useCallback } from 'react';

// Define possible connection statuses
type ConnectionStatus = 'connecting' | 'open' | 'closing' | 'closed' | 'error';

interface WebSocketHookOptions {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  shouldConnect?: boolean; // Allow conditionally connecting
}

// Define the structure of messages received from the backend
// Adjust based on your actual backend message structure
interface BackendMessage {
  type: string; // e.g., 'challenge.update', 'participant.update', 'error'
  payload: any; // The actual data payload
}

export function useWebSocket(
  url: string | null, // Pass null to prevent connection initially
  options: WebSocketHookOptions = {}
) {
  const { onOpen, onClose, onError, shouldConnect = true } = options;

  const socketRef = useRef<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<BackendMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('closed');

  useEffect(() => {
    // Only connect if a valid URL is provided and shouldConnect is true
    if (!url || !shouldConnect) {
      setConnectionStatus('closed');
      return;
    }

    // Prevent multiple connections
    if (socketRef.current && socketRef.current.readyState < 2) { // 0=CONNECTING, 1=OPEN
        console.warn("WebSocket already connecting or open.");
        return;
    }

    console.log(`useWebSocket: Attempting to connect to ${url}`);
    setConnectionStatus('connecting');
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = (event: Event) => {
      console.log(`WebSocket opened: ${url}`, event);
      setConnectionStatus('open');
      if (onOpen) onOpen(event);
    };

    socket.onmessage = (event: MessageEvent) => {
      console.log(`WebSocket message received: ${url}`, event.data);
      try {
        const parsedData: BackendMessage = JSON.parse(event.data);
        setLastMessage(parsedData); // Store the most recent message
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        // Handle non-JSON messages or errors if necessary
      }
    };

    socket.onerror = (event: Event) => {
      console.error(`WebSocket error: ${url}`, event);
      setConnectionStatus('error');
      if (onError) onError(event);
    };

    socket.onclose = (event: CloseEvent) => {
      console.log(`WebSocket closed: ${url}`, event);
      setConnectionStatus('closed');
      socketRef.current = null; // Clear ref on close
      if (onClose) onClose(event);
    };

    // Cleanup function: Close WebSocket connection when component unmounts or URL/shouldConnect changes
    return () => {
      if (socketRef.current) {
        console.log(`useWebSocket: Closing connection to ${url}`);
        setConnectionStatus('closing');
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [url, shouldConnect, onOpen, onClose, onError]); // Re-run effect if URL or options change

  // Function to send messages (optional, use REST API for primary actions)
  const sendMessage = useCallback((message: string | object) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const dataToSend = typeof message === 'string' ? message : JSON.stringify(message);
      socketRef.current.send(dataToSend);
    } else {
      console.error('WebSocket is not open. Cannot send message.');
    }
  }, []);

  return { lastMessage, connectionStatus, sendMessage };
}
```

### Authentication

As mentioned, authentication is handled via the standard Django session cookie established during HTTP login. Ensure:

1. The Next.js app and the Django backend are served from domains where the browser correctly sends the `sessionid` cookie (check CORS settings and `SESSION_COOKIE_DOMAIN`, `SESSION_COOKIE_SAMESITE` in Django if issues arise, especially across different subdomains or ports locally).
2. The `AuthMiddlewareStack` is correctly configured in your Django `asgi.py`.

No specific token or credentials need to be sent over the WebSocket connection itself.

### Handling Incoming Messages

The `useWebSocket` hook provides the `lastMessage` state variable. Your component should use a `useEffect` hook to react to changes in `lastMessage` and update its own state accordingly.

```typescript
// Example within a component:
import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket'; // Adjust path

interface ChallengeData {
  id: number;
  status: string;
  challenger: { username: string; /* ... */ };
  opponent: { username: string; /* ... */ } | null;
  attempts: Array<{ userId: number; score: number; isReady: boolean }>;
  // Add other relevant fields based on your serializers
}

function ChallengeDisplay({ challengeId }: { challengeId: number | null }) {
  const wsBaseUrl = process.env.NEXT_PUBLIC_WS_BASE_URL;
  const challengeWsUrl = challengeId ? `${wsBaseUrl}/challenges/${challengeId}/` : null;

  const [challengeData, setChallengeData] = useState<ChallengeData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Connect only if we have a challengeId
  const { lastMessage, connectionStatus } = useWebSocket(challengeWsUrl, {
      shouldConnect: !!challengeId
  });

  // Effect to process incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      setError(null); // Clear previous errors on new message
      console.log("Processing message:", lastMessage);

      switch (lastMessage.type) {
        case 'challenge.update':
        case 'challenge.start': // Contains initial state often
        case 'challenge.end':   // Contains final state
          // Assuming payload matches ChallengeDetailSerializer or ChallengeResultSerializer
          setChallengeData(lastMessage.payload as ChallengeData);
          break;
        case 'participant.update':
          // Update specific participant data within challengeData
          setChallengeData(prevData => {
            if (!prevData) return null;
            const updatedAttempt = lastMessage.payload; // Assuming payload is ChallengeAttemptSerializer data
            const userIndex = prevData.attempts.findIndex(att => att.userId === updatedAttempt.user.id); // Adjust based on actual payload structure
            if (userIndex !== -1) {
              const newAttempts = [...prevData.attempts];
              newAttempts[userIndex] = {
                  ...newAttempts[userIndex], // Keep existing fields
                  score: updatedAttempt.score,
                  isReady: updatedAttempt.is_ready,
                  // Update other fields from updatedAttempt as needed
              };
              return { ...prevData, attempts: newAttempts };
            }
            return prevData; // No change if participant not found
          });
          break;
        case 'answer.result':
           // Maybe show temporary feedback based on lastMessage.payload.is_correct
           console.log(`Answer result for Q:${lastMessage.payload.question_id}`, lastMessage.payload);
           // Score update should ideally come via participant.update
          break;
        case 'error':
          // Handle errors sent from the backend consumer
          console.error("Backend WebSocket Error:", lastMessage.payload.detail);
          setError(lastMessage.payload.detail || 'An unknown error occurred.');
          break;
        default:
          console.warn(`Unhandled WebSocket message type: ${lastMessage.type}`);
      }
    }
  }, [lastMessage]); // Re-run when lastMessage changes

  // Render based on connectionStatus and challengeData
  if (!challengeId) {
      return <div>No challenge selected.</div>;
  }

  if (connectionStatus === 'connecting') {
    return <div>Connecting to challenge...</div>;
  }

  if (connectionStatus === 'error' || connectionStatus === 'closed') {
    return <div>Connection lost or failed. Please refresh or try again. {error && `(${error})`}</div>;
  }

  if (!challengeData && connectionStatus === 'open') {
      // Fetch initial data via REST API if not sent on connect/start via WS
      // Or wait for the first 'challenge.update' or 'challenge.start' message
      return <div>Waiting for challenge data...</div>;
  }

  if (!challengeData) {
      return <div>Loading challenge data...</div>; // Or handle error state
  }

  // --- Render the actual challenge UI using challengeData ---
  return (
    <div>
      <h1>Challenge {challengeData.id}</h1>
      <p>Status: {challengeData.status} ({connectionStatus})</p>
      <p>{challengeData.challenger.username} vs {challengeData.opponent?.username || 'Waiting...'}</p>
      {/* Render scores, readiness indicators, questions etc. */}
       <div>
           <h3>Scores:</h3>
           {challengeData.attempts.map(att => (
               <p key={att.userId}>User {att.userId}: {att.score} points (Ready: {att.isReady ? 'Yes' : 'No'})</p> // Adjust user identification
           ))}
       </div>
      {/* Add buttons to trigger REST API actions (Accept, Decline, Ready, Answer) */}
    </div>
  );
}

export default ChallengeDisplay;

```

### Managing Multiple Connections

Your application might need connections to multiple endpoints simultaneously:

1. **Challenge-Specific Connection:** `/ws/challenges/{challengeId}/` (for updates within *that* specific challenge). Use the hook as shown in the `ChallengeDisplay` example.
2. **General Notifications Connection:** `/ws/challenges/notifications/` (for *new* invites, acceptance notifications, etc., for the logged-in user). You would likely manage this connection in a higher-level component (e.g., your main layout or a dedicated notification provider) using the `useWebSocket` hook with the notification URL.

```typescript
// Example in _app.tsx or a Layout component
import { useWebSocket } from '../hooks/useWebSocket';
import { useEffect } from 'react';
// Assume useAuth hook provides authentication status
import { useAuth } from '../context/AuthContext';

function GlobalNotificationHandler() {
  const { isAuthenticated } = useAuth(); // Check if user is logged in
  const wsBaseUrl = process.env.NEXT_PUBLIC_WS_BASE_URL;
  const notificationsUrl = isAuthenticated ? `${wsBaseUrl}/challenges/notifications/` : null;

  const { lastMessage } = useWebSocket(notificationsUrl, { shouldConnect: isAuthenticated });

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'new_challenge_invite') {
        console.log('Received new challenge invite!', lastMessage.payload);
        // Trigger a UI notification (e.g., using react-toastify or similar)
        // Potentially update a global list of pending invites in state management
      }
      // Handle other notification types (challenge_accepted, declined, etc.)
    }
  }, [lastMessage]);

  return null; // This component doesn't render anything itself
}

// Then include <GlobalNotificationHandler /> in your main layout
```

### State Management

* For data specific to one component (like the active challenge details), local `useState` within that component might be sufficient.
* For data needed across multiple components (like notification counts, pending invites, user points), use a more global state management solution:
  * **React Context API:** Suitable for simpler global state.
  * **Zustand / Jotai:** Lightweight global state managers.
  * **Redux / Redux Toolkit:** More robust solution for complex state.

Update your global state within the `useEffect` hook that processes `lastMessage`.

### Error Handling & Reconnection

The basic `useWebSocket` hook handles basic error logging. For production applications, consider:

* **Automatic Reconnection:** Use libraries like `reconnecting-websocket` which wrap the native `WebSocket` API and handle reconnection attempts automatically with backoff strategies. You might need to adapt the custom hook or use the library directly.
* **User Feedback:** Clearly indicate connection status (connecting, open, closed, error) to the user.
* **Fallback:** Consider fetching data periodically via REST if the WebSocket connection fails persistently.

### Key Server Event Types (`type` field in messages)

| Event Type (`type`)             | Consumer Target            | Payload Content (Expected)                                                                                                | Description                                                                  |
| :------------------------------ | :------------------------- | :------------------------------------------------------------------------------------------------------------------------ | :--------------------------------------------------------------------------- |
| `challenge.update`              | `ChallengeConsumer`        | Serialized `ChallengeDetail` data                                                                                         | General update to the challenge state (status, participants, etc.).           |
| `participant.update`            | `ChallengeConsumer`        | Serialized `ChallengeAttempt` data                                                                                        | Update for a specific participant (e.g., `is_ready`, `score`).                 |
| `challenge.start`               | `ChallengeConsumer`        | Object containing `id`, `status`, `started_at`, `challenge_config`, and serialized `questions` list.                      | Signals the challenge has started, provides initial questions.                |
| `answer.result`                 | `ChallengeConsumer`        | Object containing `user_id`, `question_id`, `is_correct`, `selected_answer`, `current_score`.                             | Immediate feedback after a user submits an answer.                          |
| `challenge.end`                 | `ChallengeConsumer`        | Serialized `ChallengeResult` data (includes final scores, winner, etc.)                                                   | Signals the challenge has completed, provides final results.                  |
| `error`                         | `ChallengeConsumer`        | `{"detail": "Error message from backend"}`                                                                                | A specific error occurred processing an action or within the consumer.     |
| `new_challenge_invite`          | `NotificationConsumer`     | Serialized `ChallengeList` data (for the new challenge)                                                                   | Notifies the user they have received a new challenge invitation.             |
| `challenge_accepted_notification` | `NotificationConsumer`     | `{"challenge_id": number, "accepted_by": string}`                                                                         | Notifies the challenger that their invite was accepted.                     |
| `challenge_declined_notification` | `NotificationConsumer`     | `{"challenge_id": number, "declined_by": string}`                                                                         | Notifies the challenger that their invite was declined.                     |
| `challenge_cancelled_notification`| `NotificationConsumer`     | `{"challenge_id": number, "cancelled_by": string}`                                                                        | Notifies the opponent (if invited) that the challenge was cancelled.        |

*(Note: Event type strings like `new.challenge.invite` in the Python `notify_user` helper should match the consumer handler methods like `new_challenge_invite`. Adjust if necessary for consistency).*
