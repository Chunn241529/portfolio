// API URL configuration
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://4f91-2a09-bac5-d46d-18d2-00-279-5a.ngrok-free.app';  // Thay thế bằng URL ngrok của bạn

function toggleChat() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.classList.toggle('active');
}

function toggleAttachMenu() {
    const menu = document.getElementById('attachMenu');
    menu.classList.toggle('active');
}

function createMessageElement(content, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

    const markdownContent = document.createElement('div');
    markdownContent.className = 'markdown-content';

    if (isUser) {
        markdownContent.textContent = content;
    } else {
        // Convert markdown to HTML
        markdownContent.innerHTML = marked.parse(content, {
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                } else {
                    return hljs.highlightAuto(code).value;
                }
            }
        });
    }

    messageDiv.appendChild(markdownContent);
    return messageDiv;
}

let isUserScrolling = false;
let lastScrollTop = 0;

function handleChatScroll(e) {
    const chatBody = e.target;
    const currentScrollTop = chatBody.scrollTop;

    // Detect if user is scrolling up
    if (currentScrollTop < lastScrollTop) {
        isUserScrolling = true;
    }

    // If user scrolls to bottom, enable auto-scroll again
    if (chatBody.scrollHeight - chatBody.scrollTop === chatBody.clientHeight) {
        isUserScrolling = false;
    }

    lastScrollTop = currentScrollTop;
}

function autoScrollChat() {
    if (!isUserScrolling) {
        const chatBody = document.getElementById('chatBody');
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const chatBody = document.getElementById('chatBody');
    const message = input.value.trim();
    if (!message) return;

    // Display user message
    const userMessage = createMessageElement(message, true);
    chatBody.appendChild(userMessage);
    input.value = '';
    autoScrollChat();

    // Send message to backend
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message
        })
    });

    // Handle streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    // Create AI message container
    const aiMessage = createMessageElement('', false);
    chatBody.appendChild(aiMessage);
    const aiContent = aiMessage.querySelector('.markdown-content');
    let fullResponse = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        fullResponse += chunk;
        aiContent.innerHTML = marked.parse(fullResponse, {
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                } else {
                    return hljs.highlightAuto(code).value;
                }
            }
        });
        autoScrollChat();
    }
}

function downloadCV() {
    const cvUrl = 'https://github.com/Chunn241529/portfolio/raw/main/static/cv/VuongNguyenTrung_Tester_QC_CV.pdf';
    window.open(cvUrl, '_blank');
}
