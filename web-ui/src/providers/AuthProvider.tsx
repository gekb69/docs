import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextProps {
    token: string | null;
    login: (service: string, apiKey?: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    loading: boolean;
}

const AuthContext = createContext<AuthContextProps>({
    token: null,
    login: async () => {},
    logout: () => {},
    isAuthenticated: false,
    loading: true,
});

export const useAuth = () => useContext(AuthContext);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [token, setToken] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const init = async () => {
            const storedToken = localStorage.getItem('sa_token');
            if (storedToken) {
                // Verify token on startup
                try {
                    const response = await fetch(`${process.env.REACT_APP_API_URL}/auth/verify`, {
                        headers: { Authorization: `Bearer ${storedToken}` },
                    });
                    if (!response.ok) throw new Error('Invalid token');
                    setToken(storedToken);
                } catch (error) {
                    console.error('Token verification failed:', error);
                    logout();
                }
            }
            setLoading(false);
        };
        init();
    }, []);

    const login = async (service: string, apiKey?: string) => {
        try {
            const url = apiKey
                ? `${process.env.REACT_APP_API_URL}/auth/verify?api_key=${apiKey}`
                : `${process.env.REACT_APP_API_URL}/auth/token?service=${service}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error('Authentication failed');

            const data = await response.json();
            const newToken = data.token || apiKey;

            setToken(newToken);
            localStorage.setItem('sa_token', newToken);
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    };

    const logout = () => {
        setToken(null);
        localStorage.removeItem('sa_token');
    };

    const value = {
        token,
        login,
        logout,
        isAuthenticated: !!token,
        loading,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
