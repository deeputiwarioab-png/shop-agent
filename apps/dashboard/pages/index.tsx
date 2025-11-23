import React, { useState } from 'react';
import Head from 'next/head';

export default function Home() {
    const [shopUrl, setShopUrl] = useState('');
    const [apiToken, setApiToken] = useState('');
    const [status, setStatus] = useState('');

    const handleSync = async () => {
        setStatus('Syncing products... This may take a while.');
        try {
            // Use environment variable or fallback to production URL
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://shop-agent-backend-prod-c3lyao3wuq-uc.a.run.app';

            const response = await fetch(`${apiUrl}/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ shop_url: shopUrl, api_token: apiToken })
            });

            if (!response.ok) {
                throw new Error(`Sync failed with status: ${response.status}`);
            }

            setStatus('Sync started! Check backend logs for progress.');
        } catch (error) {
            console.error(error);
            setStatus('Error syncing products. Check console for details.');
        }
    };

    return (
        <div style={{ fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <Head>
                <title>Shop Agent Dashboard</title>
            </Head>

            <h1>AI Shop Agent Dashboard</h1>

            <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
                <h2>Configuration</h2>
                <div style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Shopify URL:</label>
                    <input
                        type="text"
                        value={shopUrl}
                        onChange={(e) => setShopUrl(e.target.value)}
                        placeholder="my-shop.myshopify.com"
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Admin API Token:</label>
                    <input
                        type="password"
                        value={apiToken}
                        onChange={(e) => setApiToken(e.target.value)}
                        placeholder="shpat_..."
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <button
                    onClick={handleSync}
                    style={{ padding: '10px 20px', backgroundColor: '#0070f3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                    Sync Catalog
                </button>
                {status && <p style={{ marginTop: '10px', fontWeight: 'bold' }}>{status}</p>}
            </div>

            <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px' }}>
                <h2>Recent Conversations</h2>
                <p>No conversations yet.</p>
            </div>
        </div>
    );
}
