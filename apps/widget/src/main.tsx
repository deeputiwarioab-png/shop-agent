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

    console.log('Shop Agent Widget: Mounting...');

    // Mount directly to container (No Shadow DOM to avoid style isolation issues)
    ReactDOM.createRoot(container).render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    )
    console.log('Shop Agent Widget: Mounted');
}

// Auto-mount when script loads
if (document.readyState === 'complete') {
    mount();
} else {
    window.addEventListener('load', mount);
}
