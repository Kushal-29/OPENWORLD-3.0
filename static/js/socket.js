console.log("=== socket.js: Loading ===");

// Detect protocol and device
var protocol = window.location.protocol === 'https:' ? 'https' : 'http';
var host = window.location.host;
var userAgent = navigator.userAgent;
var isMobileDevice = /Mobile|Android|iPhone|iPad|iPod|BlackBerry|Windows Phone|Tablet/i.test(userAgent);

console.log("Protocol: " + protocol);
console.log("Host: " + host);
console.log("Device Type: " + (isMobileDevice ? 'MOBILE' : 'DESKTOP'));
console.log("User Agent: " + userAgent.substring(0, 100));

// ✅ CRITICAL FIX: Create socket immediately
console.log("Creating socket connection...");

var globalSocket = io({
    transports: isMobileDevice 
        ? ["polling", "websocket"]
        : ["websocket", "polling"],
    path: '/socket.io/',
    reconnection: true,
    reconnectionDelay: isMobileDevice ? 1000 : 500,
    reconnectionDelayMax: isMobileDevice ? 180000 : 60000,
    reconnectionAttempts: 999999,
    upgrade: !isMobileDevice,
    secure: protocol === 'https:',
    rejectUnauthorized: false,
    connect_timeout: isMobileDevice ? 120000 : 60000,
    rememberUpgrade: false,
    forceNew: false,
    multiplex: true,
    autoConnect: true,
    query: {
        device: isMobileDevice ? 'mobile' : 'desktop'
    }
});

console.log("Socket ID: " + globalSocket.id);

// ✅ CRITICAL FIX: Wait for actual connection before marking ready
globalSocket.on('connect', function() {
    console.log("=== ✅ SOCKET CONNECTED ===");
    console.log("Socket ID: " + globalSocket.id);
    
    var transportName = "unknown";
    if (globalSocket.io && globalSocket.io.engine && globalSocket.io.engine.transport) {
        transportName = globalSocket.io.engine.transport.name;
    }
    
    console.log("Transport: " + transportName);
    console.log("Device: " + (isMobileDevice ? "MOBILE" : "DESKTOP"));
    console.log("=====================================");
    
    window.socketError = null;
    window.socketConnected = true;
    
    // Emit user connected event
    globalSocket.emit('user_connected');
    console.log("✅ Emitted: user_connected");
});

globalSocket.on('disconnect', function(reason) {
    console.warn("=== 🔴 SOCKET DISCONNECTED ===");
    console.warn("Reason: " + reason);
    console.warn("=================================");
    window.socketConnected = false;
});

globalSocket.on('connect_error', function(error) {
    console.error("=== ⚠️ CONNECTION ERROR ===");
    console.error("Error: " + error);
    console.error("===========================");
    window.socketError = error;
});

globalSocket.on('error', function(error) {
    console.error("=== 🔴 SOCKET ERROR ===");
    console.error("Error: " + error);
    console.error("=======================");
    window.socketError = error;
});

globalSocket.on('reconnect_attempt', function(attemptNumber) {
    console.log("↻ Reconnection attempt #" + attemptNumber);
});

globalSocket.on('reconnect', function() {
    console.log("=== ✅ SUCCESSFULLY RECONNECTED ===");
    window.socketConnected = true;
    globalSocket.emit('user_connected');
    console.log("====================================");
});

globalSocket.on('reconnect_failed', function() {
    console.error("=== ❌ RECONNECTION FAILED ===");
    window.socketConnected = false;
});

// User connected event handler
globalSocket.on('user_connected', function() {
    console.log("Received: user_connected");
});

// Expose to window for other scripts
window.Socket = globalSocket;
window.io = io;
window.isMobileDevice = isMobileDevice;
window.globalSocket = globalSocket;
window.socketConnected = false;
window.socketError = null;

console.log("=== socket.js: Ready ===");
console.log("window.Socket accessible: " + (window.Socket ? "YES" : "NO"));
console.log("Socket connected: " + (globalSocket && globalSocket.connected ? "YES" : "NO"));
console.log("Device type: " + (isMobileDevice ? "MOBILE" : "DESKTOP"));
console.log("================================");

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    console.log("Page unloading, disconnecting socket...");
    if (globalSocket && globalSocket.connected) {
        globalSocket.disconnect();
        console.log("Socket disconnected on page unload");
    }
});

// Handle visibility changes (tab visibility / app background)
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log("📱 Page hidden");
    } else {
        console.log("📱 Page visible, reconnecting socket if needed...");
        if (globalSocket && !globalSocket.connected) {
            globalSocket.connect();
        }
    }
});

// Handle online/offline events (important for mobile)
window.addEventListener('online', function() {
    console.log("🌐 Device came online");
    if (globalSocket && !globalSocket.connected) {
        globalSocket.connect();
    }
});

window.addEventListener('offline', function() {
    console.warn("📴 Device went offline");
});

console.log("=== socket.js: Initialization Complete ===");