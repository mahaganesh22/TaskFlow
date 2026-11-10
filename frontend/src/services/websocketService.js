
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000";

class AuthenticatedWebSocket {
  constructor({
    path,
    getAccessToken,
    refreshAccessToken,
    onEvent,
    onStatusChange,
    onReconnect,
    onAuthError
  }) {
    this.path = path;
    this.getAccessToken = getAccessToken;
    this.onEvent = onEvent;
    this.refreshAccessToken = refreshAccessToken;
    this.authRefreshAttempted = false;
    this.refreshedToken = null;
    this.onStatusChange = onStatusChange;
    this.onReconnect = onReconnect;
    this.onAuthError = onAuthError;

    this.socket = null;
    this.reconnectTimer = null;
    this.reconnectAttempts = 0;
    this.hasConnectedBefore = false;
    this.shouldReconnect = true;
    this.connectionId = 0;
  }

  updateStatus(status) {
    this.onStatusChange?.(status);
  }

  async connect() {
    if (!this.shouldReconnect) return;

    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
       this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    const currentConnectionId = ++this.connectionId;

    this.updateStatus(
      this.hasConnectedBefore ? "reconnecting" : "connecting"
    );

    try {
        const token = this.refreshedToken || await this.getAccessToken();
        this.refreshedToken = null;

      // Ignore this attempt if the connection was closed while
      // the access token was being retrieved.
      if (
        !this.shouldReconnect ||
        currentConnectionId !== this.connectionId
      ) {
        return;
      }

      if (!token) {
        this.updateStatus("unauthenticated");
        this.onAuthError?.();
        return;
      }

      const socket = new WebSocket(`${WS_BASE_URL}${this.path}`);

      this.socket = socket;

      socket.onopen = () => {
        if (this.socket !== socket) return;

        this.updateStatus("authenticating");

        socket.send(JSON.stringify({
          type: "authenticate",
          token
        }));
      };

      socket.onmessage = (event) => {
        if (this.socket !== socket) return;

        let message;

        try {
          message = JSON.parse(event.data);
        } catch {
          return;
        }

        if (message.type === "CONNECTED") {
          const isReconnect = this.hasConnectedBefore;

          this.hasConnectedBefore = true;
          this.reconnectAttempts = 0;
          this.authRefreshAttempted = false;

          this.updateStatus("connected");

          if (isReconnect) {
            this.onReconnect?.();
          }

          return;
        }

        this.onEvent?.(message);
      };

      socket.onclose = async (event) => {
        if (this.socket === socket) {
          this.socket = null;
        }

        if (!this.shouldReconnect) return;

        // These codes indicate authentication or authorization
        // failure. Retrying the same connection won't fix them.
        if (event.code === 4401) {
            if (!this.authRefreshAttempted && this.refreshAccessToken) {
                this.authRefreshAttempted = true;

                try {
                    const newToken = await this.refreshAccessToken();

                    if (newToken && this.shouldReconnect) {
                        this.refreshedToken = newToken;
                        this.connect();
                        return;
                    }
                } catch (error) {
                    console.error("Token refresh failed:", error);
                }
            }

            this.updateStatus("unauthenticated");
            this.onAuthError?.(4401);
            return;
        }

        if (event.code === 4403) {
            this.updateStatus("forbidden");
            this.onAuthError?.(4403);
            return;
        }

        this.updateStatus("disconnected");
        this.scheduleReconnect();
      };

      socket.onerror = () => {
        // The browser normally fires onclose after onerror.
        // Reconnection is handled in onclose.
      };

    } catch (error) {
      console.error("WebSocket connection failed:", error);

      if (this.shouldReconnect) {
        this.updateStatus("disconnected");
        this.scheduleReconnect();
      }
    }
  }

  scheduleReconnect() {
    if (!this.shouldReconnect || this.reconnectTimer) return;

    this.reconnectAttempts += 1;

    // Exponential backoff, capped at 30 seconds.
    const delay = Math.min(
      1000 * (2 ** (this.reconnectAttempts - 1)),
      30000
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  disconnect() {
    this.shouldReconnect = false;

    // Invalidate any pending token retrieval.
    this.connectionId += 1;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      const socket = this.socket;
      this.socket = null;
      socket.close(1000, "Client disconnected");
    }

    this.updateStatus("disconnected");
  }
}

export default AuthenticatedWebSocket;
