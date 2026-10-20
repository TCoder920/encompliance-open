/*
  Description: Secure login page for customer support agents.
  Purpose: Authenticates support staff before granting access to the support portal.
*/

import React, { useState } from 'react';
import customerSupportApi from '../services/customerSupportApi';

interface CustomerSupportLoginPageProps {
    onLoginSuccess: (token: string) => void;
}

const CustomerSupportLoginPage: React.FC<CustomerSupportLoginPageProps> = ({ onLoginSuccess }) => {
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            // Send as URL-encoded form data for OAuth2PasswordRequestForm compatibility
            // FastAPI's OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
            const params = new URLSearchParams();
            params.set('username', username);
            params.set('password', password);
            
            // We use the customerSupportApi instance, but we need to override the Content-Type header
            // and ensure we don't send an auth token (which shouldn't be set yet anyway)
            // The baseURL is already set in customerSupportApi (e.g. /api or http://localhost:6050)
            // Note: customerSupportApi might have interceptors, but for login it should be fine.
            // If customerSupportApi has a baseURL of /api (proxy), then we post to /auth/token.
            
            // We need to import customerSupportApi first.
            const response = await customerSupportApi.post('/auth/token', params, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            const data = response.data;
            if (data.access_token) {
                onLoginSuccess(data.access_token);
            } else {
                throw new Error('Login failed: No access token received');
            }

        } catch (err: any) {
            console.error("Customer Support Login Error:", err);
            // Handle axios errors
            const status = err.response?.status;
            const errorData = err.response?.data || {};
            
            if (status === 401) {
                setError('Invalid username or password.');
            } else if (status === 422) {
                // FastAPI validation errors can be an array or a single object
                const detail = errorData.detail;
                let errorMsg = 'Validation error. Please check your input.';
                if (Array.isArray(detail) && detail.length > 0) {
                    errorMsg = detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
                } else if (typeof detail === 'string') {
                    errorMsg = detail;
                } else if (detail && typeof detail === 'object') {
                    errorMsg = detail.msg || detail.message || JSON.stringify(detail);
                }
                console.error("422 Error details:", JSON.stringify(detail, null, 2));
                setError(errorMsg);
            } else {
                const detail = errorData.detail;
                const errorMsg = typeof detail === 'string' ? detail : (err.message || 'Unknown error');
                setError(`Login failed: ${errorMsg}`);
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg transition-colors duration-1000">
            <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-md w-full max-w-md">
                <h1 className="text-2xl font-bold mb-6 text-center text-gray-800 dark:text-white">Customer Support Portal</h1>
                {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">{error}</div>}
                <form onSubmit={handleLogin}>
                    <div className="mb-4">
                        <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="username">
                            Username
                        </label>
                        <input
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 dark:border-gray-600 leading-tight focus:outline-none focus:shadow-outline"
                            id="username"
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={isLoading}
                            autoComplete="username"
                        />
                    </div>
                    <div className="mb-6">
                        <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="password">
                            Password
                        </label>
                        <input
                            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 dark:border-gray-600 mb-3 leading-tight focus:outline-none focus:shadow-outline"
                            id="password"
                            type="password"
                            placeholder="******************"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={isLoading}
                            autoComplete="current-password"
                        />
                    </div>
                    <div className="flex items-center justify-between">
                        <button
                            type="submit"
                            disabled={isLoading}
                            className={`w-full py-2 px-4 rounded font-bold transition duration-200 ${isLoading ? 'opacity-50 cursor-not-allowed bg-gray-300 dark:bg-gray-700 text-gray-500' : 'bg-navy-blue text-white hover:bg-blue-800 dark:bg-blue-700 dark:hover:bg-blue-800'}`}
                        >
                            {isLoading ? 'Logging in...' : 'Enter Workspace'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CustomerSupportLoginPage;