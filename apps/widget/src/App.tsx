import { useState } from 'react'

// Simple styles for the widget
const styles = {
    container: {
        position: 'fixed' as const,
        bottom: '20px',
        right: '20px',
        zIndex: 2147483647, // Maximum z-index value
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
        width: '380px',
        height: '600px',
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
    productCard: {
        backgroundColor: '#fff',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '12px',
        marginTop: '8px',
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
    },
    productImage: {
        width: '60px',
        height: '60px',
        objectFit: 'cover' as const,
        borderRadius: '4px',
    },
    productInfo: {
        flex: 1,
    },
    productTitle: {
        fontWeight: 'bold',
        fontSize: '14px',
        marginBottom: '4px',
    },
    productPrice: {
        color: '#666',
        fontSize: '13px',
    },
    cartButton: {
        marginTop: '8px',
        width: '100%',
        padding: '6px 12px',
        backgroundColor: '#000',
        color: '#fff',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        fontSize: '12px',
        fontWeight: 'bold',
    }
};

interface Product {
    id: string;
    title: string;
    image_url?: string;
    price?: string;
    handle?: string;
    default_variant_id?: string;
}

interface Message {
    id: string;
    text: string;
    isUser: boolean;
    products?: Product[];
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
            const apiUrl = 'https://shop-agent-backend-c3lyao3wuq-uc.a.run.app';
            const response = await fetch(`${apiUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg.text })
            });

            const data = await response.json();

            // Use structured product data from backend
            const products = data.products || [];
            const responseText = data.response;

            const botMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: responseText || 'Here are some products I found:',
                isUser: false,
                products
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { id: Date.now().toString(), text: 'Sorry, something went wrong.', isUser: false }]);
        } finally {
            setIsLoading(false);
        }
    };

    // Carousel navigation
    const [carouselIndices, setCarouselIndices] = useState<{ [key: string]: number }>({});

    const nextProduct = (msgId: string, total: number) => {
        setCarouselIndices(prev => ({
            ...prev,
            [msgId]: ((prev[msgId] || 0) + 1) % total
        }));
    };

    const prevProduct = (msgId: string, total: number) => {
        setCarouselIndices(prev => ({
            ...prev,
            [msgId]: ((prev[msgId] || 0) - 1 + total) % total
        }));
    };

    return (
        <div style={styles.container}>
            {isOpen && (
                <div style={styles.window}>
                    <div style={styles.header}>Shopping Assistant</div>
                    <div style={styles.messages}>
                        {messages.map(msg => (
                            <div key={msg.id}>
                                <div style={styles.messageBubble(msg.isUser)}>
                                    {msg.text}
                                </div>
                                {msg.products && msg.products.length > 0 && (
                                    <div style={{ marginTop: '12px', position: 'relative' }}>
                                        {/* Carousel Container */}
                                        <div style={styles.productCard}>
                                            {(() => {
                                                const currentIndex = carouselIndices[msg.id] || 0;
                                                const product = msg.products[currentIndex];
                                                return (
                                                    <>
                                                        {product.image_url ? (
                                                            <img
                                                                src={product.image_url}
                                                                alt={product.title}
                                                                style={styles.productImage}
                                                            />
                                                        ) : (
                                                            <div style={{ ...styles.productImage, backgroundColor: '#eee', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                                📷
                                                            </div>
                                                        )}
                                                        <div style={styles.productInfo}>
                                                            <div style={styles.productTitle}>{product.title}</div>
                                                            {product.price && (
                                                                <div style={styles.productPrice}>${product.price}</div>
                                                            )}

                                                            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                                                                <a
                                                                    href={product.handle ? `/products/${product.handle}` : '#'}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    style={{
                                                                        fontSize: '12px',
                                                                        color: '#0070f3',
                                                                        textDecoration: 'none',
                                                                        alignSelf: 'center'
                                                                    }}
                                                                >
                                                                    View Details
                                                                </a>
                                                                {product.default_variant_id && (
                                                                    <button
                                                                        style={{
                                                                            padding: '4px 8px',
                                                                            backgroundColor: '#000',
                                                                            color: '#fff',
                                                                            border: 'none',
                                                                            borderRadius: '4px',
                                                                            cursor: 'pointer',
                                                                            fontSize: '11px',
                                                                            marginLeft: 'auto'
                                                                        }}
                                                                        onClick={() => {
                                                                            window.location.href = `/cart/${product.default_variant_id}:1`;
                                                                        }}
                                                                    >
                                                                        Add to Cart
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </>
                                                );
                                            })()}
                                        </div>

                                        {/* Carousel Controls */}
                                        {msg.products.length > 1 && (
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', padding: '0 4px' }}>
                                                <button
                                                    onClick={() => prevProduct(msg.id, msg.products!.length)}
                                                    style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#666' }}
                                                >
                                                    ◀ Prev
                                                </button>
                                                <span style={{ fontSize: '12px', color: '#888' }}>
                                                    {(carouselIndices[msg.id] || 0) + 1} / {msg.products.length}
                                                </span>
                                                <button
                                                    onClick={() => nextProduct(msg.id, msg.products!.length)}
                                                    style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#666' }}
                                                >
                                                    Next ▶
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                        {isLoading && <div style={{ alignSelf: 'flex-start', color: '#888', fontSize: '12px', marginLeft: '12px' }}>Thinking...</div>}
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
