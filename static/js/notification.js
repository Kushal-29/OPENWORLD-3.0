// Notification System for OPENWORLD
// Handles message notifications and popups
// Uses the global Socket.IO instance from socket.js

const NotificationSystem = {
    init: function() {
        // Use global Socket instead of creating new one
        if (!window.Socket) {
            console.error("❌ Socket not available for notifications!");
            return;
        }
        
        const socket = window.Socket;
        console.log("✅ NotificationSystem initialized");
        
        // Emit user connected event for notifications
        socket.emit('user_connected');

        // Listen for message notifications (popup)
        socket.on('message_notification', (data) => {
            this.showNotificationPopup(data);
            this.playNotificationSound();
        });

        // Listen for message read status
        socket.on('message_read', (data) => {
            this.updateReadStatus(data);
        });

        // Listen for chat list updates
        socket.on('chat_list_update', () => {
            this.refreshFriendsList();
        });
    },

    showNotificationPopup: function(data) {
        // Create notification container if it doesn't exist
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification-popup';
        notification.style.cssText = `
            background: #FFFFFF;
            color: #000000;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            display: flex;
            gap: 12px;
            align-items: flex-start;
            animation: slideIn 0.3s ease;
            cursor: pointer;
            min-width: 300px;
        `;

        // Avatar
        const avatar = document.createElement('img');
        avatar.src = data.sender_avatar || '/static/uploads/profiles/default.png';
        avatar.style.cssText = `
            width: 48px;
            height: 48px;
            border-radius: 50%;
            object-fit: cover;
            flex-shrink: 0;
        `;
        avatar.onerror = function() {
            this.src = '/static/uploads/profiles/default.png';
        };

        // Content
        const content = document.createElement('div');
        content.style.cssText = `
            flex: 1;
            min-width: 0;
        `;

        const sender = document.createElement('div');
        sender.textContent = data.sender_name;
        sender.style.cssText = `
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 4px;
        `;

        const message = document.createElement('div');
        message.textContent = data.message_text;
        message.style.cssText = `
            font-size: 13px;
            color: #666666;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        `;

        content.appendChild(sender);
        content.appendChild(message);

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: #666666;
            font-size: 16px;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        `;

        closeBtn.onclick = (e) => {
            e.stopPropagation();
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        };

        notification.appendChild(avatar);
        notification.appendChild(content);
        notification.appendChild(closeBtn);

        // Click to open chat
        notification.onclick = () => {
            window.location.href = `/chat/${data.sender_id}`;
        };

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    },

    playNotificationSound: function() {
        // Optional: Play notification sound
        // You can add an audio file later
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.5;
        audio.play().catch(() => {
            // Fail silently if audio not available
        });
    },

    updateReadStatus: function(data) {
        // Update message read status in UI
        const messageEl = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (messageEl) {
            // Mark as read visually
            messageEl.classList.add('message-read');
        }

        // Remove unread badge from friends list
        this.refreshFriendsList();
    },

    refreshFriendsList: function() {
        // Reload friends list to update unread counts
        // This happens automatically when friends_list page is loaded
        // For other pages, you might want to fetch and update dynamically
    }
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    .notification-popup {
        will-change: transform;
    }

    .message-read {
        opacity: 0.7;
    }
`;
document.head.appendChild(style);

// Initialize when page loads (if socket is ready)
document.addEventListener('DOMContentLoaded', () => {
    // Wait for socket to be ready
    if (window.Socket && window.Socket.connected) {
        NotificationSystem.init();
    } else {
        // Wait for socket connection
        let checkSocket = setInterval(() => {
            if (window.Socket && window.Socket.connected) {
                NotificationSystem.init();
                clearInterval(checkSocket);
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(() => clearInterval(checkSocket), 5000);
    }
});