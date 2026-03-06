/**
 * OPENWORLD MATCH.JS - COMPLETE WORKING VERSION
 * Handles real-time video matching with WebRTC
 * ✅ All event names match backend (match_events.py)
 */

console.log("🚀 match.js: Initializing...");

let socket = null;
let localStream = null;
let peerConnection = null;
let roomId = null;
let isSearching = false;
let strangerName = null;
let strangerId = null;

// ===== DOM ELEMENTS =====
const statusEl = document.getElementById("status");
const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const startBtn = document.getElementById("startBtn");
const skipBtn = document.getElementById("skipBtn");
const endBtn = document.getElementById("endBtn");
const addFriendBtn = document.getElementById("addFriendBtn");

// ===== WEBRTC CONFIG =====
const servers = {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" },
        { urls: "stun:stun2.l.google.com:19302" },
        { urls: "stun:stun3.l.google.com:19302" },
        { 
            urls: "turn:openrelay.metered.ca:443", 
            username: "openrelayproject", 
            credential: "openrelayproject" 
        }
    ]
};

// ===== INITIALIZATION =====

function init() {
    console.log("⚙️ Initializing match system...");
    
    // Get global socket from socket.js
    if (!window.Socket) {
        console.error("❌ Socket not available! Waiting...");
        setTimeout(init, 500);
        return;
    }
    
    socket = window.Socket;
    console.log("✅ Socket acquired:", socket.id);
    
    // Setup event listeners
    setupSocketListeners();
    
    // Setup button listeners
    setupButtonListeners();
    
    console.log("🎉 Match system ready!");
}

// ===== BUTTON LISTENERS =====

function setupButtonListeners() {
    if (startBtn) {
        startBtn.addEventListener('click', findMatch);
        console.log("✅ Start button ready");
    }
    
    if (skipBtn) {
        skipBtn.addEventListener('click', skipMatch);
        console.log("✅ Skip button ready");
    }
    
    if (endBtn) {
        endBtn.addEventListener('click', endMatch);
        console.log("✅ End button ready");
    }
    
    if (addFriendBtn) {
        addFriendBtn.addEventListener('click', addFriend);
        console.log("✅ Add Friend button ready");
    }
}

// ===== STATUS UPDATE =====

function setStatus(text) {
    console.log("[Status]", text);
    if (statusEl) {
        statusEl.textContent = text;
    }
}

function updateButtonVisibility(state) {
    console.log("Button state:", state);
    
    if (!startBtn || !skipBtn || !endBtn || !addFriendBtn) {
        console.warn("Some buttons not found in DOM");
        return;
    }
    
    // Hide all
    startBtn.style.display = "none";
    skipBtn.style.display = "none";
    endBtn.style.display = "none";
    addFriendBtn.style.display = "none";
    
    // Show relevant ones
    switch(state) {
        case "idle":
            startBtn.style.display = "block";
            break;
        case "searching":
            // Show nothing while searching
            break;
        case "matched":
            skipBtn.style.display = "block";
            endBtn.style.display = "block";
            addFriendBtn.style.display = "block";
            break;
    }
}

// ===== MEDIA HANDLING =====

async function startMedia() {
    try {
        console.log("📹 Requesting camera...");
        
        if (localStream) {
            console.log("⚠️ Stream already active");
            return;
        }
        
        localStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "user"
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        console.log("✅ Camera started");
        
        if (localVideo) {
            localVideo.srcObject = localStream;
            console.log("✅ Video displayed locally");
        }
        
        return true;
    } catch (error) {
        console.error("❌ Camera error:", error.message);
        setStatus("❌ Camera: " + error.message);
        return false;
    }
}

function stopLocalStream() {
    if (localStream) {
        localStream.getTracks().forEach(track => {
            track.stop();
            console.log("🛑 Track stopped:", track.kind);
        });
        localStream = null;
        if (localVideo) {
            localVideo.srcObject = null;
        }
    }
}

// ===== WEBRTC PEER CONNECTION =====

function createPeerConnection() {
    console.log("🔌 Creating WebRTC peer connection...");
    
    peerConnection = new RTCPeerConnection(servers);
    console.log("✅ Peer connection created");
    
    // Add local tracks
    if (localStream) {
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
            console.log("✅ Added track:", track.kind);
        });
    }
    
    // Handle remote tracks
    peerConnection.ontrack = (event) => {
        console.log("📹 Remote track received:", event.track.kind);
        
        if (remoteVideo && event.streams[0]) {
            remoteVideo.srcObject = event.streams[0];
            remoteVideo.play().catch(err => {
                console.warn("Play error:", err);
            });
            setStatus("✅ Video connected!");
            console.log("✅ Remote video playing");
        }
    };
    
    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
        if (event.candidate && roomId) {
            console.log("🧊 Sending ICE candidate");
            socket.emit("webrtc_ice_candidate", {
                room: roomId,
                candidate: event.candidate
            });
        }
    };
    
    // Handle connection state changes
    peerConnection.onconnectionstatechange = () => {
        console.log("Connection state:", peerConnection.connectionState);
        
        if (["failed", "disconnected", "closed"].includes(peerConnection.connectionState)) {
            console.warn("❌ Connection lost");
            setStatus("❌ Connection lost");
            setTimeout(() => {
                cleanupPeerConnection();
            }, 1000);
        }
    };
}

function cleanupPeerConnection() {
    console.log("Cleaning up peer connection...");
    
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    
    if (remoteVideo) {
        remoteVideo.srcObject = null;
    }
    
    roomId = null;
}

async function createAndSendOffer() {
    try {
        console.log("📤 Creating WebRTC offer...");
        
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        
        console.log("✅ Offer created, sending to peer...");
        
        socket.emit("webrtc_offer", {
            room: roomId,
            offer: peerConnection.localDescription
        });
        
        console.log("✅ Offer sent");
    } catch (error) {
        console.error("❌ Offer creation failed:", error);
    }
}

// ===== MATCH ACTIONS =====

async function findMatch() {
    console.log("\n🔍 FIND_MATCH: Starting...\n");
    
    if (isSearching) {
        console.warn("Already searching");
        return;
    }
    
    try {
        // Start camera
        setStatus("📹 Starting camera...");
        const cameraOk = await startMedia();
        
        if (!cameraOk) {
            console.error("Camera failed");
            return;
        }
        
        // Update UI
        isSearching = true;
        updateButtonVisibility("searching");
        setStatus("⏳ Searching for a stranger...");
        
        // Emit to backend
        console.log("📤 Emitting: start_search");
        socket.emit("start_search");
        
        console.log("✅ Search started\n");
        
    } catch (error) {
        console.error("❌ Error starting match:", error);
        isSearching = false;
        updateButtonVisibility("idle");
        setStatus("❌ Error: " + error.message);
    }
}

function skipMatch() {
    console.log("\n⏭️ SKIP_MATCH\n");
    
    if (!isSearching) {
        cleanupPeerConnection();
        isSearching = true;
        updateButtonVisibility("searching");
        setStatus("⏳ Finding next stranger...");
    }
    
    console.log("📤 Emitting: skip_stranger");
    socket.emit("skip_stranger");
}

function endMatch() {
    console.log("\n🛑 END_MATCH\n");
    
    stopLocalStream();
    cleanupPeerConnection();
    isSearching = false;
    updateButtonVisibility("idle");
    setStatus('📱 Click "Start" to find another match');
    
    console.log("📤 Emitting: end_chat");
    socket.emit("end_chat");
}

function addFriend() {
    console.log("\n❤️ ADD_FRIEND\n");
    
    if (!roomId || !strangerId) {
        console.error("No active match");
        return;
    }
    
    console.log("📤 Emitting: send_friend_request_during_chat");
    socket.emit("send_friend_request_during_chat", {
        room: roomId,
        stranger_id: strangerId
    });
}

// ===== SOCKET LISTENERS =====

function setupSocketListeners() {
    console.log("\n🔌 Setting up socket listeners...\n");
    
    // ===== MATCH FOUND =====
    socket.on("match_confirmed", (data) => {
        console.log("\n🎉 MATCH_CONFIRMED\n", data, "\n");
        
        roomId = data.room;
        strangerName = data.stranger_name;
        strangerId = data.stranger_id;
        isSearching = false;
        
        // Update UI
        updateButtonVisibility("matched");
        setStatus("📹 Connected to " + strangerName);
        
        // Create peer connection
        createPeerConnection();
        
        // If we're the initiator, send offer
        if (data.your_role === "initiator") {
            console.log("You are initiator - sending offer");
            setTimeout(() => createAndSendOffer(), 500);
        } else {
            console.log("You are receiver - waiting for offer");
        }
    });
    
    // ===== WEBRTC OFFER =====
    socket.on("webrtc_offer", async (data) => {
        console.log("📥 Received WebRTC offer");
        
        try {
            if (!peerConnection) {
                createPeerConnection();
            }
            
            await peerConnection.setRemoteDescription(
                new RTCSessionDescription(data.offer)
            );
            
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            
            console.log("✅ Sending WebRTC answer");
            socket.emit("webrtc_answer", {
                room: roomId,
                answer: peerConnection.localDescription
            });
        } catch (error) {
            console.error("❌ Offer handling failed:", error);
        }
    });
    
    // ===== WEBRTC ANSWER =====
    socket.on("webrtc_answer", async (data) => {
        console.log("📥 Received WebRTC answer");
        
        try {
            await peerConnection.setRemoteDescription(
                new RTCSessionDescription(data.answer)
            );
            console.log("✅ Answer processed");
        } catch (error) {
            console.error("❌ Answer handling failed:", error);
        }
    });
    
    // ===== ICE CANDIDATE =====
    socket.on("webrtc_ice_candidate", async (data) => {
        try {
            if (peerConnection && peerConnection.remoteDescription) {
                await peerConnection.addIceCandidate(
                    new RTCIceCandidate(data.candidate)
                );
            }
        } catch (error) {
            console.warn("⚠️ ICE candidate error:", error);
        }
    });
    
    // ===== STATUS UPDATES =====
    socket.on("status", (message) => {
        console.log("📊 Status:", message);
        setStatus(message);
    });
    
    // ===== STRANGER DISCONNECTED =====
    socket.on("stranger_disconnected", () => {
        console.log("\n👋 STRANGER_DISCONNECTED\n");
        
        cleanupPeerConnection();
        stopLocalStream();
        isSearching = false;
        updateButtonVisibility("idle");
        setStatus('Stranger left. Click "Start" to find another.');
    });
    
    // ===== STRANGER SKIPPED =====
    socket.on("stranger_skipped", () => {
        console.log("\n⏭️ STRANGER_SKIPPED\n");
        
        cleanupPeerConnection();
        isSearching = false;
        updateButtonVisibility("idle");
        setStatus('Stranger skipped. Click "Start" to continue.');
    });
    
    // ===== RESET =====
    socket.on("reset", () => {
        console.log("\n🔄 RESET\n");
        
        cleanupPeerConnection();
        stopLocalStream();
        isSearching = false;
        updateButtonVisibility("idle");
        setStatus('Click "Start" to begin matching.');
    });
    
    // ===== FRIEND ADDED =====
    socket.on("friend_added_notification", (data) => {
        console.log("✅ Friend added notification:", data);
    });
    
    socket.on("friend_added", (message) => {
        console.log("✅ Friend added:", message);
        setStatus(message);
    });
    
    // ===== ERRORS =====
    socket.on("error", (message) => {
        console.error("❌ Socket error:", message);
        setStatus("❌ " + message);
    });
    
    console.log("✅ All socket listeners registered\n");
}

// ===== PAGE CLEANUP =====

window.addEventListener("beforeunload", () => {
    console.log("Page unloading, cleaning up...");
    stopLocalStream();
    cleanupPeerConnection();
    socket.emit("end_chat");
});

document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
        console.log("📱 Page hidden - pausing video");
        if (localStream) {
            localStream.getTracks().forEach(track => {
                track.enabled = false;
            });
        }
    } else {
        console.log("📱 Page visible - resuming video");
        if (localStream) {
            localStream.getTracks().forEach(track => {
                track.enabled = true;
            });
        }
    }
});

// ===== START =====

document.addEventListener("DOMContentLoaded", init);

// If page is already loaded
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}

console.log("✅ match.js loaded and ready");