document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const themeToggle = document.querySelector('.theme-toggle');
    
    // Theme handling
    const theme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', theme);
    themeToggle.innerHTML = theme === 'light' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        themeToggle.innerHTML = newTheme === 'light' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
    });

    // Chat form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        userInput.value = '';
        
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        
        try {
            // Send message to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // Handle source command
            if (message.toLowerCase() === 'source') {
                handleSourceCommand(data);
                return;
            }
            
            // Add bot response to chat
            addMessage(data.response, 'bot');
            
            // Update source info if it's a scrape command
            if (message.toLowerCase().startsWith('scrape:')) {
                updateSourceInfo(data);
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, an error occurred while processing your request.', 'bot');
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });

    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Handle markdown-like formatting
        content = formatMessage(content);
        
        messageContent.innerHTML = content;
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatMessage(content) {
        // Convert URLs to links
        content = content.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Convert bullet points
        content = content.replace(/^\s*[-*]\s+(.+)/gm, '<li>$1</li>');
        content = content.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Convert code blocks
        content = content.replace(/\`\`\`([\s\S]*?)\`\`\`/g, '<pre><code>$1</code></pre>');
        content = content.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
        
        return content;
    }

    function handleSourceCommand(data) {
        const sourceInfo = document.getElementById('sourceInfo');
        const currentSource = document.getElementById('currentSource');
        
        if (data.source) {
            currentSource.innerHTML = `
                <strong>URL:</strong> ${data.source.url}<br>
                ${data.source.title ? `<strong>Title:</strong> ${data.source.title}<br>` : ''}
                <strong>Scraped at:</strong> ${new Date(data.source.timestamp).toLocaleString()}
            `;
        } else {
            currentSource.textContent = 'No source has been scraped yet.';
        }
        
        sourceInfo.style.display = 'flex';
    }

    function updateSourceInfo(data) {
        if (data.source) {
            const currentSource = document.getElementById('currentSource');
            currentSource.innerHTML = `
                <strong>URL:</strong> ${data.source.url}<br>
                ${data.source.title ? `<strong>Title:</strong> ${data.source.title}<br>` : ''}
                <strong>Scraped at:</strong> ${new Date(data.source.timestamp).toLocaleString()}
            `;
        }
    }
});

function toggleSourceInfo() {
    const sourceInfo = document.getElementById('sourceInfo');
    sourceInfo.style.display = 'none';
}
