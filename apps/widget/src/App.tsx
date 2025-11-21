import React, { useState } from 'react'

// Simple styles for the widget
const styles = {
    container: {
        position: 'fixed' as const,
        bottom: '20px',
        right: '20px',
        zIndex: 99999,
        fontFamily: 'Arial, sans-serif',
    },
    button: {
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        backgroundColor: '#000',
        color: '#fff',
        border: 'none',
        cursor: 'pointer',
        fontSize: '24px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
    window: {
        position: 'absolute' as const,
        bottom: '80px',
        right: '0',
        width: '350px',
        height: '500px',
        backgroundColor: '#fff',
        borderRadius: '12px',
        boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
        display: 'flex',
        flexDirection: 'column' as const,
        overflow: 'hidden',
    },
    header: {
        padding: '16px',
        backgroundColor: '#f4f4f4',
        borderBottom: '1px solid #e0e0e0',
        fontWeight: 'bold',
    },
    messages: {
        flex: 1,
        padding: '16px',
        overflowY: 'auto' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        gap: '12px',
    },
    inputArea: {
        padding: '16px',
        borderTop: '1px solid #e0e0e0',
        display: 'flex',
        gap: '8px',
    },
    input: {
        flex: 1,
        padding: '8px 12px',
        borderRadius: '20px',
        border: '1px solid #ddd',
        outline: 'none',
    },
    sendButton: {
        padding: '8px 16px',
        borderRadius: '20px',
        backgroundColor: '#000',
        color: '#fff',
        border: 'none',
        cursor: 'pointer',
    },
    messageBubble: (isUser: boolean) => ({
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        backgroundColor: isUser ? '#000' : '#f0f0f0',
        color: isUser ? '#fff' : '#000',
        padding: '8px 12px',
        borderRadius: '12px',
        maxWidth: '80%',
        wordWrap: 'break-word' as const,
    }),
};

interface Message {
    id: string;
    text: string;
    isUser: boolean;
}

function App() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        { id: '1', text: 'Hi! How can I help you shop today?', isUser: false }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const toggleOpen = () => setIsOpen(!isOpen);

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const userMsg: Message = { id: Date.now().toString(), text: inputValue, isUser: true };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsLoading(true);

        try {
            // In production, this URL should be configurable or relative if proxied
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg.text })
            });

            const data = await response.json();
            const botMsg: Message = { id: (Date.now() + 1).toString(), text: data.response, isUser: false };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { id: Date.now().toString(), text: 'Sorry, something went wrong.', isUser: false }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            {isOpen && (
                <div style={styles.window}>
                    <div style={styles.header}>Shopping Assistant</div>
                    <div style={styles.messages}>
                        {messages.map(msg => (
                            <div key={msg.id} style={styles.messageBubble(msg.isUser)}>
                                {msg.text}
                            </div>
                        ))}
                        {isLoading && <div style={{ alignSelf: 'flex-start', color: '#888' }}>Thinking...</div>}
                    </div>
                    <div style={styles.inputArea}>
                        <input
                            style={styles.input}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Ask about products..."
                        />
                        <button style={styles.sendButton} onClick={handleSend}>Send</button>
                    </div>
                </div>
            )}
            <button style={styles.button} onClick={toggleOpen}>
                {isOpen ? '✕' : '💬'}
            </button>
        </div>
    )
}

export default App
