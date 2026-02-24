/**
 * MATCH.JS - Omegle-Style Random Video Chat
 * COMPLETELY REWRITTEN - Proper flow control and error handling
 */

console.log("✅ match.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    console.log("🎮 Initializing video chat...");

    // Wait for socket
    let socket = null;
    let retries = 0;
    
    const checkSocket = setInterval(() => {
        if (window.Socket && window.Socket.connected) {
            socket = window.Socket;
            clearInterval(checkSocket);
            console.log("✅ Socket ready");
            initializeVideoChat();
        } else {
            retries++;
            if (retries >= 20) {
                clearInterval(checkSocket);
                alert("❌ Failed to connect to server");
            }
        }
    }, 100);

    function initializeVideoChat() {
        // DOM Elements
        const localVideo = document.getElementById("localVideo");
        const remoteVideo = document.getElementById("remoteVideo");
        const statusEl = document.getElementById("status");
        
        const startBtn = document.getElementById("startBtn");
        const skipBtn = document.getElementById("skipBtn");
        const endBtn = document.getElementById("endBtn");
        const addFriendBtn = document.getElementById("addFriendBtn");

        // State
        let localStream = null;
        let pc = null;
        let roomId = null;
        let strangerId = null;
        let strangerName = null;
        let isStarting = false;        // Currently requesting camera
        let isSearching = false;       // Currently waiting for match
        let isConnected = false;       // Currently in video call
        let pendingIce = [];

        const iceServers = {
            iceServers: [
                { urls: "stun:stun.l.google.com:19302" },
                { urls: "stun:stun1.l.google.com:19302" },
                { urls: "stun:stun2.l.google.com:19302" },
                {
                    urls: "turn:openrelay.metered.ca:443",
                    username: "openrelayproject",
                    credential: "openrelayproject"
                }
            ]
        };

        // ========== LOGGING ==========
        function setStatus(text) {
            console.log("📝 Status:", text);
            if (statusEl) statusEl.textContent = text;
        }

        function log(msg) {
            console.log(msg);
        }

        // ========== UI STATES ==========
        
        function showIdleUI() {
            log("🎨 UI: IDLE - waiting for user to click Start");
            startBtn.style.display = "inline-block";
            skipBtn.style.display = "none";
            endBtn.style.display = "none";
            addFriendBtn.style.display = "none";
            startBtn.disabled = false;
            setStatus('📱 Click "Start" to find a stranger');
        }

        function showRequestingCameraUI() {
            log("🎨 UI: REQUESTING CAMERA");
            startBtn.style.display = "none";
            skipBtn.style.display = "none";
            endBtn.style.display = "none";
            addFriendBtn.style.display = "none";
            setStatus("📹 Requesting camera and microphone...");
        }

        function showSearchingUI() {
            log("🎨 UI: SEARCHING - waiting for match");
            startBtn.style.display = "none";
            skipBtn.style.display = "inline-block";
            endBtn.style.display = "inline-block";
            addFriendBtn.style.display = "none";
            setStatus("🔍 Searching for a stranger...");
        }

        function showConnectingUI() {
            log("🎨 UI: CONNECTING - WebRTC negotiation");
            startBtn.style.display = "none";
            skipBtn.style.display = "inline-block";
            endBtn.style.display = "inline-block";
            addFriendBtn.style.display = "none";
            setStatus("⏳ Connecting to stranger...");
        }

        function showConnectedUI(name) {
            log("🎨 UI: CONNECTED - video active");
            startBtn.style.display = "none";
            skipBtn.style.display = "inline-block";
            endBtn.style.display = "inline-block";
            addFriendBtn.style.display = "inline-block";
            setStatus(`✅ Connected to ${name}!`);
            isConnected = true;
        }

        function showErrorUI(error) {
            log("🎨 UI: ERROR - " + error);
            startBtn.style.display = "inline-block";
            skipBtn.style.display = "none";
            endBtn.style.display = "none";
            addFriendBtn.style.display = "none";
            startBtn.disabled = false;
            setStatus(error);
        }

        // ========== CAMERA REQUEST ==========
        
        async function requestCamera() {
            return new Promise((resolve, reject) => {
                log("🎬 Step 1: REQUESTING CAMERA");
                log("  User needs to ALLOW camera permission");
                
                showRequestingCameraUI();
                isStarting = true;

                // Set timeout for permission request
                const permissionTimeout = setTimeout(() => {
                    log("⏰ TIMEOUT: Camera permission took too long");
                    isStarting = false;
                    reject(new Error("Camera permission timeout - user did not respond or blocked"));
                }, 20000); // 20 second timeout

                navigator.mediaDevices.getUserMedia({
                    video: { 
                        width: { ideal: 1280 }, 
                        height: { ideal: 720 } 
                    },
                    audio: true
                })
                .then(stream => {
                    clearTimeout(permissionTimeout);
                    log("✅ CAMERA APPROVED: Got media stream");
                    isStarting = false;
                    localStream = stream;
                    
                    // Show video immediately
                    if (localVideo) {
                        localVideo.srcObject = stream;
                        localVideo.play().catch(e => log("Play error: " + e));
                        log("✅ Local video displaying");
                    }
                    
                    resolve(stream);
                })
                .catch(error => {
                    clearTimeout(permissionTimeout);
                    log("❌ CAMERA ERROR: " + error.name);
                    isStarting = false;
                    
                    let msg = "❌ Camera Error";
                    if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                        msg = "❌ You BLOCKED camera. Enable it in browser settings.";
                    } else if (error.name === "NotFoundError") {
                        msg = "❌ No camera found. Check hardware.";
                    } else if (error.name === "NotReadableError") {
                        msg = "❌ Camera is in use. Close other video apps.";
                    } else if (error.name === "AbortError") {
                        msg = "❌ Camera request was cancelled.";
                    }
                    
                    reject(new Error(msg));
                });
            });
        }

        // ========== SEARCH FOR MATCH ==========
        
        async function sendSearchRequest() {
            return new Promise((resolve, reject) => {
                log("🔍 Step 2: SENDING SEARCH REQUEST");
                log("  Waiting for server to find another user...");
                
                showSearchingUI();
                isSearching = true;

                // Timeout if no match after 3 minutes
                const searchTimeout = setTimeout(() => {
                    log("⏰ TIMEOUT: No match found in 3 minutes");
                    isSearching = false;
                    reject(new Error("No strangers available - try again later"));
                }, 180000); // 3 minutes

                // Listen for match
                socket.once("match_confirmed", (data) => {
                    clearTimeout(searchTimeout);
                    log("🎉 MATCH FOUND!");
                    log(`  Other user: ${data.stranger_name}`);
                    log(`  Room: ${data.room}`);
                    isSearching = false;
                    
                    roomId = data.room;
                    strangerId = data.stranger_id;
                    strangerName = data.stranger_name;
                    
                    resolve(data);
                });

                // Send search to server
                log("  Emitting 'start_search' to server");
                socket.emit("start_search");
            });
        }

        // ========== WEBRTC CONNECTION ==========
        
        function createPeerConnection() {
            log("🔗 Step 3A: CREATE PEER CONNECTION");
            
            if (pc) {
                log("  Already exists, skipping");
                return pc;
            }

            pc = new RTCPeerConnection(iceServers);
            log("  RTCPeerConnection created");

            // Add local tracks
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    log(`  Adding track: ${track.kind}`);
                    pc.addTrack(track, localStream);
                });
            }

            // Handle remote stream
            pc.ontrack = (event) => {
                log(`📹 Received remote track: ${event.track.kind}`);
                
                if (event.streams && event.streams[0]) {
                    remoteVideo.srcObject = event.streams[0];
                } else {
                    const stream = new MediaStream();
                    stream.addTrack(event.track);
                    remoteVideo.srcObject = stream;
                }

                remoteVideo.play().catch(e => log("Remote play error: " + e));
                log("✅ Remote video displaying");
            };

            // Handle ICE candidates
            pc.onicecandidate = (event) => {
                if (event.candidate) {
                    log("🧊 Sending ICE candidate");
                    socket.emit("webrtc_ice_candidate", {
                        room: roomId,
                        candidate: event.candidate
                    });
                }
            };

            // Monitor connection
            pc.onconnectionstatechange = () => {
                log(`🔗 Connection state: ${pc.connectionState}`);

                if (pc.connectionState === "connected") {
                    log("✅✅✅ WEBRTC CONNECTED! ✅✅✅");
                    showConnectedUI(strangerName);
                }

                if (["failed", "disconnected", "closed"].includes(pc.connectionState)) {
                    log("❌ Connection lost: " + pc.connectionState);
                    cleanup();
                    setStatus("Stranger disconnected. Searching...");
                    setTimeout(() => handleStart(), 2000);
                }
            };

            log("✅ PeerConnection ready");
            return pc;
        }

        async function createAndSendOffer() {
            log("🔗 Step 3B: CREATE OFFER (initiator role)");
            
            try {
                const offer = await pc.createOffer();
                log("  Offer created");
                
                await pc.setLocalDescription(offer);
                log("  Local description set");
                
                socket.emit("webrtc_offer", { room: roomId, offer });
                log("  Offer sent to stranger");
                
            } catch (error) {
                log("❌ Offer error: " + error);
                throw error;
            }
        }

        function waitForAnswer() {
            log("🔗 Step 3C: WAITING FOR ANSWER (receiver role)");
            log("  Waiting for stranger's answer...");
        }

        async function flushIceQueue() {
            log(`🧊 Flushing ${pendingIce.length} queued ICE candidates`);
            
            for (const candidate of pendingIce) {
                try {
                    await pc.addIceCandidate(candidate);
                } catch (error) {
                    log("ICE add error: " + error);
                }
            }
            pendingIce = [];
            log("✅ ICE queue flushed");
        }

        function cleanup() {
            log("🧹 CLEANUP");
            
            if (pc) {
                pc.close();
                pc = null;
                log("  Closed PeerConnection");
            }
            
            if (remoteVideo) remoteVideo.srcObject = null;
            
            roomId = null;
            strangerId = null;
            strangerName = null;
            pendingIce = [];
            isConnected = false;
            isSearching = false;
            
            log("✅ Cleanup complete");
        }

        // ========== BUTTON HANDLERS ==========
        
        async function handleStart() {
            log("\n🎮 ===== START BUTTON CLICKED =====\n");

            if (isStarting || isSearching || isConnected) {
                log("  Already in progress, ignoring");
                return;
            }

            try {
                // Step 1: Request camera
                log("STEP 1: Get camera permission");
                await requestCamera();
                log("✅ Step 1 complete\n");

                // Step 2: Search for match
                log("STEP 2: Search for another stranger");
                const matchData = await sendSearchRequest();
                log("✅ Step 2 complete\n");

                // Step 3: WebRTC
                log("STEP 3: Start WebRTC connection");
                showConnectingUI();
                
                createPeerConnection();
                
                if (matchData.your_role === "initiator") {
                    log("  Role: INITIATOR (you create offer)");
                    await createAndSendOffer();
                } else {
                    log("  Role: RECEIVER (wait for offer)");
                    waitForAnswer();
                }
                log("✅ Step 3 complete\n");

            } catch (error) {
                log("\n❌ ERROR: " + error.message + "\n");
                showErrorUI(error.message);
                cleanup();
                isStarting = false;
                isSearching = false;
            }
        }

        function handleSkip() {
            log("\n⏭️ ===== SKIP BUTTON CLICKED =====\n");
            
            socket.emit("skip_stranger");
            cleanup();
            
            log("Auto-restarting search...");
            setTimeout(() => handleStart(), 1000);
        }

        function handleEnd() {
            log("\n🛑 ===== END BUTTON CLICKED =====\n");
            
            socket.emit("end_chat");
            cleanup();
            
            log("Returning to idle state");
            showIdleUI();
        }

        function handleAddFriend() {
            log("\n❤️ ===== ADD FRIEND BUTTON CLICKED =====\n");
            
            if (roomId && strangerId) {
                socket.emit("send_friend_request_during_chat", {
                    room: roomId,
                    stranger_id: strangerId
                });
            }
        }

        // Attach button handlers
        startBtn.onclick = handleStart;
        skipBtn.onclick = handleSkip;
        endBtn.onclick = handleEnd;
        addFriendBtn.onclick = handleAddFriend;

        // ========== SOCKET LISTENERS ==========
        
        socket.on("webrtc_offer", async (data) => {
            log("\n📥 Received WebRTC offer from stranger");
            
            try {
                const offer = new RTCSessionDescription({
                    type: "offer",
                    sdp: data.offer.sdp || data.offer
                });

                await pc.setRemoteDescription(offer);
                log("  Remote description (offer) set");
                
                await flushIceQueue();

                const answer = await pc.createAnswer();
                log("  Answer created");
                
                await pc.setLocalDescription(answer);
                log("  Local description set");
                
                socket.emit("webrtc_answer", { room: roomId, answer });
                log("  Answer sent back\n");

            } catch (error) {
                log("❌ Offer handling error: " + error);
            }
        });

        socket.on("webrtc_answer", async (data) => {
            log("\n📥 Received WebRTC answer from stranger");
            
            try {
                const answer = new RTCSessionDescription({
                    type: "answer",
                    sdp: data.answer.sdp || data.answer
                });

                await pc.setRemoteDescription(answer);
                log("  Remote description (answer) set");
                
                await flushIceQueue();
                log("  Ready for ICE candidates\n");

            } catch (error) {
                log("❌ Answer handling error: " + error);
            }
        });

        socket.on("webrtc_ice_candidate", async (data) => {
            try {
                // Queue if not ready
                if (!pc || !pc.remoteDescription) {
                    log("🧊 Queueing ICE (not ready yet)");
                    pendingIce.push(data.candidate);
                    return;
                }

                await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                log("🧊 ICE added");

            } catch (error) {
                log("ICE error: " + error);
            }
        });

        socket.on("stranger_disconnected", (data) => {
            log("\n⚠️ Stranger disconnected: " + data.message);
            showErrorUI(data.message);
            cleanup();
            setTimeout(() => handleStart(), 2000);
        });

        socket.on("stranger_skipped", (data) => {
            log("\n⏭️ Stranger skipped you");
            cleanup();
            showSearchingUI();
        });

        socket.on("status", (data) => {
            log("📡 Server status: " + data);
            setStatus(data);
        });

        socket.on("error", (data) => {
            log("❌ Server error: " + data);
            showErrorUI(data);
        });

        // Cleanup on page leave
        window.addEventListener("beforeunload", () => {
            if (localStream) {
                localStream.getTracks().forEach(t => t.stop());
            }
            cleanup();
        });

        // Start idle
        showIdleUI();
        log("\n✅ VIDEO CHAT READY - Click Start\n");
    }
});