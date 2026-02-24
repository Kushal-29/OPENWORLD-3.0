// Chat functionality - Uses global Socket.IO instance from socket.js
console.log("✅ chat.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    console.log("🎬 Chat page initializing...");

    // Use the global socket from socket.js (not create a new one)
    if (!window.Socket) {
        console.error("❌ Socket not available!");
        alert("Connection error. Please refresh the page.");
        return;
    }

    const socket = window.Socket;
    const messagesContainer = document.getElementById('messagesContainer');
    const chatData = document.getElementById('chatData');
    const messageInput = document.getElementById('messageInput');

    if (!chatData) {
        console.warn("⚠️ chatData element not found");
        return;
    }

    const room = chatData.dataset.room;
    const friendId = parseInt(chatData.dataset.friendId);
    const currentUserId = parseInt(chatData.dataset.currentUser);

    console.log(`📍 Room: ${room}, Friend: ${friendId}, User: ${currentUserId}`);

    // Join the chat room
    socket.emit('join_chat', { room: room });
    console.log(`✅ Joined room: ${room}`);

    // ================= RECEIVE MESSAGE =================
    socket.on('receive_message', (data) => {
        console.log("📥 Message received:", data);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.sender_id === currentUserId ? 'sent' : 'received'}`;
        messageDiv.dataset.messageId = data.id;

        let content = '<div class="message-content">';

        if (data.text) {
            content += `<div class="message-text">${escapeHtml(data.text)}</div>`;
        }

        if (data.image) {
            content += `<div class="message-image"><img src="/static/uploads/chat/${data.image}" alt="Image" onerror="this.src='/static/images/error.png'" style="max-width: 100%; border-radius: 8px;"></div>`;
        }

        if (data.document) {
            content += `<a href="/static/uploads/chat/${data.document}" class="message-text" style="display: inline-flex; align-items: center; gap: 8px;">📄 ${escapeHtml(data.document)}</a>`;
        }

        content += `<div class="message-time">${data.timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>`;
        content += '</div>';

        messageDiv.innerHTML = content;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Mark as read if we're the receiver
        if (data.sender_id !== currentUserId && data.id) {
            setTimeout(() => {
                socket.emit('mark_as_read', { message_id: data.id });
            }, 500);
        }
    });

    // ================= CHAT LIST UPDATE =================
    socket.on('chat_list_update', () => {
        console.log("🔄 Chat list needs update");
        // Reload the page to get updated friend list
        // Or emit an event to update counts dynamically
    });

    // ================= MESSAGE READ STATUS =================
    socket.on('message_read', (data) => {
        console.log("✓ Message read:", data.message_id);
        const msgEl = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (msgEl) {
            msgEl.classList.add('message-read');
        }
    });

    // ================= SEND MESSAGE =================
    function sendMessage() {
        const text = messageInput.value.trim();

        if (!text) {
            console.log("⚠️ Empty message");
            return;
        }

        console.log("📤 Sending message:", text.substring(0, 50));

        socket.emit('send_message', {
            room: room,
            receiver_id: friendId,
            text: text
        });

        messageInput.value = '';
        messageInput.focus();
    }

    // ================= KEY PRESS HANDLING =================
    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    // ================= EMOJI HANDLING =================
    function insertEmoji(emoji) {
        messageInput.value += emoji;
        messageInput.focus();
        toggleEmojiPicker();
    }

    function toggleEmojiPicker() {
        const picker = document.getElementById('emojiPicker');
        if (picker) {
            picker.classList.toggle('active');
        }
    }

    // ================= HTML ESCAPING =================
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // ================= FILE UPLOAD =================
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            console.log("📤 Uploading file:", file.name);

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/upload-chat-file', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    console.log("✅ File uploaded:", data.filename);
                    
                    socket.emit('send_message', {
                        room: room,
                        receiver_id: friendId,
                        image: data.filename
                    });

                    // Reset file input
                    fileInput.value = '';
                } else {
                    alert("Upload failed: " + data.error);
                }
            } catch (error) {
                console.error('❌ Upload error:', error);
                alert("Error uploading file");
            }
        });
    }

    // ================= ATTACH HANDLERS =================
    if (messageInput) {
        messageInput.addEventListener('keypress', handleKeyPress);
    }

    // Make functions available globally for onclick handlers
    window.sendMessage = sendMessage;
    window.handleKeyPress = handleKeyPress;
    window.insertEmoji = insertEmoji;
    window.toggleEmojiPicker = toggleEmojiPicker;
    window.escapeHtml = escapeHtml;

    console.log("✅ Chat initialized successfully");
});