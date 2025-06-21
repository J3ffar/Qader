import { useState, useEffect, useRef, useCallback } from "react";

// Define possible connection statuses
export type ConnectionStatus =
  | "connecting"
  | "open"
  | "closing"
  | "closed"
  | "error";

// This is the expected structure of messages from our Django Channels backend.
export interface WebSocketMessage {
  type: string;
  payload: any;
}

interface WebSocketHookOptions {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  shouldConnect?: boolean;
}

export function useWebSocket(
  url: string | null,
  options: WebSocketHookOptions = {}
) {
  const { onOpen, onClose, onError, shouldConnect = true } = options;
  const socketRef = useRef<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("closed");

  useEffect(() => {
    if (!url || !shouldConnect) {
      if (socketRef.current) socketRef.current.close();
      return;
    }

    if (socketRef.current && socketRef.current.readyState < 2) {
      // 0=CONNECTING, 1=OPEN
      return;
    }

    setConnectionStatus("connecting");
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = (event) => {
      setConnectionStatus("open");
      if (onOpen) onOpen(event);
    };

    socket.onmessage = (event: MessageEvent) => {
      try {
        const parsedData: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(parsedData);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    socket.onerror = (event) => {
      console.error(`WebSocket error: ${url}`, event);
      setConnectionStatus("error");
      if (onError) onError(event);
    };

    socket.onclose = (event) => {
      setConnectionStatus("closed");
      socketRef.current = null;
      if (onClose) onClose(event);
    };

    return () => {
      if (socketRef.current) {
        setConnectionStatus("closing");
        socketRef.current.close();
      }
    };
  }, [url, shouldConnect, onOpen, onClose, onError]);

  const sendMessage = useCallback((message: string | object) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const dataToSend =
        typeof message === "string" ? message : JSON.stringify(message);
      socketRef.current.send(dataToSend);
    } else {
      console.error("WebSocket is not open. Cannot send message.");
    }
  }, []);

  return { lastMessage, connectionStatus, sendMessage };
}
