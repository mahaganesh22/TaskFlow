
import { useEffect, useRef, useState } from "react";
import AuthenticatedWebSocket from "../services/websocketService";

export default function useUserWebSocket({
  enabled = true,
  getAccessToken,
  onEvent,
  refreshAccessToken,
  onReconnect,
  onAuthError
}) {
  const [status, setStatus] = useState("disconnected");

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
    if (!enabled) {
      setStatus("disconnected");
      return;
    }

    const connection = new AuthenticatedWebSocket({
      path: "/ws/users/me",

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
  }, [enabled]);

  return { status };
}
