
import { useEffect, useRef, useState } from "react";
import AuthenticatedWebSocket from "../services/websocketService";

export default function useProjectWebSocket({
  projectId,
  getAccessToken,
  onEvent,
  refreshAccessToken,
  onReconnect,
  onAuthError
}) {
  const [status, setStatus] = useState("disconnected");

  // Keep the latest callbacks without reconnecting the socket
  // whenever a component creates a new callback function.
  const callbacksRef = useRef({});
  const tokenGetterRef = useRef(getAccessToken);
  const refreshTokenRef = useRef(refreshAccessToken);

  callbacksRef.current = {
    onEvent,
    onReconnect,
    onAuthError
  };

  tokenGetterRef.current = getAccessToken;
  refreshTokenRef.current = refreshAccessToken;

  useEffect(() => {
    if (!projectId) {
      setStatus("disconnected");
      return;
    }

    const connection = new AuthenticatedWebSocket({
      path: `/ws/projects/${projectId}`,

      getAccessToken: () => tokenGetterRef.current(),
      
      refreshAccessToken: () => refreshTokenRef.current(),

      onEvent: (message) => {
        callbacksRef.current.onEvent?.(message);
      },

      onStatusChange: (nextStatus) => {
        setStatus(nextStatus);
      },

      onReconnect: () => {
        callbacksRef.current.onReconnect?.();
      },

      onAuthError: (code) => {
        callbacksRef.current.onAuthError?.(code);
      }
    });

    connection.connect();

    return () => {
      connection.disconnect();
    };
  }, [projectId]);

  return { status };
}
