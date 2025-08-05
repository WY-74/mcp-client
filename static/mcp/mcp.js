// MCP Chat Interface JavaScript

class MCPChat {
    constructor() {
        this.isConnected = false;
        this.isLoading = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.showWelcomeMessage();
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

    showWelcomeMessage() {
        const welcomeMsg = "Welcome to MCP Chat! Connect to the server first, then start asking questions about weather.";
        this.addMessage(welcomeMsg, 'assistant');
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
            const response = await fetch('/mcp/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.handleConnectionSuccess();
                await this.loadTools();
                this.addMessage("Connected to MCP weather server! You can now ask weather questions.", 'assistant');
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

    handleConnectionSuccess() {
        this.isConnected = true;
        
        const statusDiv = document.getElementById('statusDiv');
        const connectBtn = document.getElementById('connectBtn');
        const queryInput = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');

        if (statusDiv) {
            statusDiv.className = 'status status-connected';
            statusDiv.textContent = 'Connected to MCP server';
        }

        if (connectBtn) {
            connectBtn.style.display = 'none';
        }

        if (queryInput) {
            queryInput.disabled = false;
            queryInput.placeholder = 'Ask a weather question...';
        }

        if (sendBtn) {
            sendBtn.disabled = false;
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

    async loadTools() {
        try {
            const response = await fetch('/mcp/tools');
            const result = await response.json();
            
            if (result.tools && result.tools.length > 0) {
                this.displayTools(result.tools);
            }
        } catch (error) {
            console.error('Error loading tools:', error);
        }
    }

    displayTools(tools) {
        const toolsSection = document.getElementById('toolsSection');
        const toolsList = document.getElementById('toolsList');
        
        if (!toolsSection || !toolsList) return;

        toolsList.innerHTML = '';
        
        tools.forEach(tool => {
            const toolDiv = document.createElement('div');
            toolDiv.className = 'tool-item';
            toolDiv.innerHTML = `
                <strong>${this.escapeHtml(tool.name)}</strong>
                ${this.escapeHtml(tool.description)}
            `;
            toolsList.appendChild(toolDiv);
        });
        
        toolsSection.style.display = 'block';
    }

    async sendQuery() {
        const queryInput = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (!queryInput || !sendBtn) return;

        const query = queryInput.value.trim();
        
        if (!query) {
            this.showInputError('Please enter a question');
            return;
        }

        if (!this.isConnected) {
            this.addMessage('Please connect to MCP server first', 'assistant');
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
            const response = await fetch('/mcp/query', {
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

    // Utility method to show examples
    showExamples() {
        const examples = [
            "Get weather alerts for CA",
            "Get forecast for latitude 37.7749, longitude -122.4194",
            "What's the weather like in San Francisco?",
            "Are there any weather warnings for Texas?"
        ];

        const exampleText = "Here are some example questions you can ask:\n\n" + 
            examples.map(ex => `• ${ex}`).join('\n');
        
        this.addMessage(exampleText, 'assistant');
    }
}

// Initialize MCP Chat when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const mcpChat = new MCPChat();
    
    // Add examples button functionality if needed
    window.showExamples = () => mcpChat.showExamples();
});
