import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

const WIDGET_ID = 'shop-agent-widget-container';

function mount() {
    // Check if already mounted
    if (document.getElementById(WIDGET_ID)) return;

    // Create container
    const container = document.createElement('div');
    container.id = WIDGET_ID;
    document.body.appendChild(container);

    // Create Shadow DOM
    const shadow = container.attachShadow({ mode: 'open' });

    // Create a mount point inside Shadow DOM
    const mountPoint = document.createElement('div');
    shadow.appendChild(mountPoint);

    // Inject styles manually if needed, or rely on vite-plugin-css-injected-by-js
    // The plugin usually injects styles into the document head, which might not penetrate Shadow DOM.
    // For a robust solution, we might need to manually fetch styles or use a different approach.
    // However, for this MVP, let's try to inject the styles into the shadow root.

    // Note: In a real production build with 'vite-plugin-css-injected-by-js', 
    // it might try to put style tags in <head>. We might need to move them or configure the plugin.
    // For now, let's assume standard React rendering.

    ReactDOM.createRoot(mountPoint).render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    )
}

// Auto-mount when script loads
if (document.readyState === 'complete') {
    mount();
} else {
    window.addEventListener('load', mount);
}
