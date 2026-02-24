console.log("✅ socket.js loaded");

// Create socket instance ONCE and expose globally
const socket = io({
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
    upgrade: true
});

socket.on("connect", () => {
    console.log("🟢 Socket connected:", socket.id);
    
    // Emit user connected event for notifications
    if (socket.connected) {
        socket.emit('user_connected');
    }
});

socket.on("disconnect", () => {
    console.warn("🔴 Socket disconnected");
});

socket.on("connect_error", (error) => {
    console.error("❌ Connection error:", error);
});

// Expose to window for use in other scripts
window.Socket = socket;
window.io = io;  // Also expose io constructor

console.log("✅ socket.js initialization complete");