import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { useAuth } from './AuthProvider';

interface WebSocketContextProps {
    connected: boolean;
    messages: any[];
    send: (data: any) => void;
    lastMessage: any | null;
}

const WebSocketContext = createContext<WebSocketContextProps>({
    connected: false,
    messages: [],
    send: () => {},
    lastMessage: null,
});

export const useWebSocket = () => useContext(WebSocketContext);

interface WebSocketProviderProps {
    children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState<any[]>([]);
    const [lastMessage, setLastMessage] = useState<any | null>(null);
    const ws = useRef<WebSocket | null>(null);
    const { token } = useAuth();

    useEffect(() => {
        if (!token) return;

        const connect = () => {
            const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
            ws.current = new WebSocket(`${wsUrl}?token=${token}`);

            ws.current.onopen = () => {
                console.log('✅ WebSocket connected');
                setConnected(true);
            };

            ws.current.onclose = () => {
                console.log('❌ WebSocket disconnected');
                setConnected(false);

                // Reconnect after 5 seconds
                setTimeout(connect, 5000);
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setMessages(prev => [...prev, data]);
                    setLastMessage(data);
                } catch (error) {
                    console.error('Failed to parse message:', error);
                }
            };
        };

        connect();

        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [token]);

    const send = (data: any) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    };

    const value = {
        connected,
        messages,
        send,
        lastMessage,
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
};
