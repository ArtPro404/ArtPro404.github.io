// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Set username in the header
    document.getElementById('username').textContent = sessionStorage.getItem('username');
    
    // Logout button
    document.getElementById('logout').addEventListener('click', function() {
        fetch('/logout', {
            method: 'GET',
            credentials: 'same-origin'
        }).then(() => {
            sessionStorage.clear();
            window.location.href = '/login';
        });
    });
    
    // Load contacts
    loadContacts();
    
    // Message sending
    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    let currentReceiver = null;
    let messagePolling = null;
    
    function loadContacts() {
        fetch('/api/users', {
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(users => {
            const contactList = document.getElementById('contact-list');
            contactList.innerHTML = '';
            
            users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = user.username;
                li.dataset.userId = user.id;
                li.addEventListener('click', function() {
                    selectContact(user.id, user.username);
                });
                contactList.appendChild(li);
            });
        });
    }
    
    function selectContact(userId, username) {
        currentReceiver = userId;
        document.getElementById('chat-with').textContent = `Chat with ${username}`;
        document.getElementById('message-input').disabled = false;
        document.getElementById('send-button').disabled = false;
        
        // Clear previous polling
        if (messagePolling) {
            clearInterval(messagePolling);
        }
        
        // Load messages
        loadMessages();
        
        // Start polling for new messages
        messagePolling = setInterval(loadMessages, 2000);
    }
    
    function loadMessages() {
        if (!currentReceiver) return;
        
        fetch(`/api/messages/${currentReceiver}`, {
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(messages => {
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = '';
            
            messages.forEach(msg => {
                const isSent = msg.sender === sessionStorage.getItem('username');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = msg.content;
                
                const timeDiv = document.createElement('div');
                timeDiv.className = 'message-timestamp';
                timeDiv.textContent = new Date(msg.timestamp).toLocaleTimeString();
                
                messageDiv.appendChild(contentDiv);
                messageDiv.appendChild(timeDiv);
                messagesContainer.appendChild(messageDiv);
            });
            
            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }
    
    function sendMessage() {
        const input = document.getElementById('message-input');
        const content = input.value.trim();
        
        if (!content || !currentReceiver) return;
        
        fetch(`/api/messages/${currentReceiver}`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        })
        .then(response => {
            if (response.ok) {
                input.value = '';
                loadMessages();
            }
        });
    }
    
    // Store username in sessionStorage for frontend use
    if (!sessionStorage.getItem('username')) {
        fetch('/api/users', {
            credentials: 'same-origin'
        })
        .then(response => {
            if (response.ok) {
                sessionStorage.setItem('username', document.getElementById('username').textContent);
            }
        });
    }
});