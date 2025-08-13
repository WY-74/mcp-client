// MCP Chat Interface JavaScript

class MCPChat {
    constructor() {
        this.isConnected = false;
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Connect button
        const connectBtn = document.getElementById('connectBtn');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connectToMCP());
        }

        // Send button
        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendQuery());
        }

        // Enter key for input
        const queryInput = document.getElementById('queryInput');
        if (queryInput) {
            queryInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !queryInput.disabled && !this.isLoading) {
                    this.sendQuery();
                }
            });
        }
    }

    async connectToMCP() {
        const connectBtn = document.getElementById('connectBtn');
        const statusDiv = document.getElementById('statusDiv');
        
        if (!connectBtn || !statusDiv) return;

        this.setLoading(true);
        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting...';
        connectBtn.classList.add('loading');
        
        try {
            const response = await fetch('/atgent/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.handleConnectionSuccess(result.message);
            } else {
                this.handleConnectionError(result.message);
            }
        } catch (error) {
            console.error('Connection error:', error);
            this.handleConnectionError('Network error occurred while connecting');
        } finally {
            this.setLoading(false);
            connectBtn.classList.remove('loading');
        }
    }

    handleConnectionSuccess(message) {
        this.isConnected = true;
        
        const statusDiv = document.getElementById('statusDiv');
        const connectBtn = document.getElementById('connectBtn');
        const queryInput = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');

        if (statusDiv) {
            statusDiv.className = 'status status-connected';
            statusDiv.style.whiteSpace = 'pre-line';
            statusDiv.textContent = message;
        }

        if (connectBtn) {
            connectBtn.style.display = 'none';
        }

        if (queryInput) {
            queryInput.style.display = 'block';
            queryInput.disabled = false;
            queryInput.placeholder = '与 ATGent 对话';
            queryInput.className = 'mcp-input';
        }

        if (sendBtn) {
            sendBtn.style.display = 'block';
            sendBtn.disabled = false;
            sendBtn.className = 'btn btn-primary';
            sendBtn.textContent = 'Send';
        }

        if (chatContainer) {
            chatContainer.style.display = 'block';
        }
    }

    handleConnectionError(message) {
        const statusDiv = document.getElementById('statusDiv');
        const connectBtn = document.getElementById('connectBtn');

        if (statusDiv) {
            statusDiv.className = 'status status-disconnected';
            statusDiv.textContent = message || 'Failed to connect to MCP server';
        }

        if (connectBtn) {
            connectBtn.disabled = false;
            connectBtn.textContent = 'Connect to MCP Server';
        }

        this.addMessage(`Connection failed: ${message}`, 'assistant');
    }

    async sendQuery() {
        const queryInput = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (!queryInput || !sendBtn) return;

        const query = queryInput.value.trim();
        
        if (!query) {
            this.showInputError('请输入你的问题');
            return;
        }

        // Add user message
        this.addMessage(query, 'user');
        queryInput.value = '';
        
        // Set loading state
        this.setLoading(true);
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';
        sendBtn.classList.add('loading');
        
        try {
            const response = await fetch('/atgent/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addMessage(result.message, 'assistant');
            } else {
                this.addMessage(`Error: ${result.message}`, 'assistant');
            }
        } catch (error) {
            console.error('Query error:', error);
            this.addMessage('Network error occurred while processing your query', 'assistant');
        } finally {
            this.setLoading(false);
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
            sendBtn.classList.remove('loading');
            queryInput.focus();
        }
    }

    addMessage(content, sender) {
        const chatContainer = document.getElementById('chatContainer');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Handle multiline content and preserve formatting
        const formattedContent = this.formatMessageContent(content);
        messageDiv.innerHTML = formattedContent;
        
        chatContainer.appendChild(messageDiv);
        
        // Smooth scroll to bottom
        requestAnimationFrame(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    }

    formatMessageContent(content) {
        // Escape HTML and preserve line breaks
        const escaped = this.escapeHtml(content);
        
        // Convert line breaks to <br> tags
        let formatted = escaped.replace(/\n/g, '<br>');
        
        // Make tool calls more readable
        formatted = formatted.replace(/\[Calling tool ([^\]]+)\]/g, 
            '<span style="color: #007bff; font-weight: bold;">🔧 Calling tool: $1</span>');
        
        return formatted;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showInputError(message) {
        const queryInput = document.getElementById('queryInput');
        if (!queryInput) return;

        queryInput.style.borderColor = '#dc3545';
        queryInput.placeholder = message;
        
        setTimeout(() => {
            queryInput.style.borderColor = '';
            queryInput.placeholder = 'Ask a weather question...';
        }, 3000);
    }

    setLoading(isLoading) {
        this.isLoading = isLoading;
        const queryInput = document.getElementById('queryInput');
        
        if (queryInput) {
            queryInput.disabled = isLoading || !this.isConnected;
        }
    }

}

// Initialize MCP Chat when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const mcpChat = new MCPChat();
});
