import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './ChatMessage';
import { MessageLimit } from './MessageLimit';
import { useAuth } from '../../contexts/AuthContext';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
}

const DAILY_MESSAGE_LIMIT = 5;

export const ChatBox: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: "Hey! I'm your AI Coach. Ask me anything about your gameplay - tips, patterns, improvement areas. What would you like to know?",
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [remainingMessages, setRemainingMessages] = useState(DAILY_MESSAGE_LIMIT);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { getIdToken } = useAuth();

    // Load remaining messages from localStorage
    useEffect(() => {
        const today = new Date().toDateString();
        const stored = localStorage.getItem('ai-chat-limit');

        if (stored) {
            const data = JSON.parse(stored);
            if (data.date === today) {
                setRemainingMessages(data.remaining);
            } else {
                // New day, reset limit
                localStorage.setItem('ai-chat-limit', JSON.stringify({ date: today, remaining: DAILY_MESSAGE_LIMIT }));
                setRemainingMessages(DAILY_MESSAGE_LIMIT);
            }
        } else {
            localStorage.setItem('ai-chat-limit', JSON.stringify({ date: today, remaining: DAILY_MESSAGE_LIMIT }));
        }
    }, []);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading || remainingMessages <= 0) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        // Decrement remaining messages
        const newRemaining = remainingMessages - 1;
        setRemainingMessages(newRemaining);
        localStorage.setItem(
            'ai-chat-limit',
            JSON.stringify({ date: new Date().toDateString(), remaining: newRemaining })
        );

        try {
            const token = await getIdToken();

            const response = await fetch(
                `${import.meta.env.VITE_API_ENDPOINT}/api/v1/chat`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token && { Authorization: `Bearer ${token}` }),
                    },
                    body: JSON.stringify({ message: userMessage.content }),
                }
            );

            if (!response.ok) throw new Error('Chat request failed');

            const data = await response.json();

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.response || "I couldn't process that request. Please try again.",
            };

            setMessages((prev) => [...prev, aiMessage]);
        } catch {
            // Fallback response if API fails
            const fallbackMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "I'm having trouble connecting right now. Please try again in a moment.",
            };
            setMessages((prev) => [...prev, fallbackMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Chat Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-r from-purple-600 to-cyan-600 shadow-lg shadow-purple-500/25 flex items-center justify-center text-2xl hover:scale-105 transition-transform"
            >
                {isOpen ? '✕' : '🤖'}
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 z-50 w-96 h-[500px] rounded-2xl bg-gray-900/95 backdrop-blur-sm border border-white/10 shadow-2xl flex flex-col overflow-hidden">
                    {/* Header */}
                    <div className="px-4 py-3 bg-gradient-to-r from-purple-600/20 to-cyan-600/20 border-b border-white/10">
                        <div className="flex items-center space-x-2">
                            <span className="text-xl">🤖</span>
                            <div>
                                <h3 className="font-semibold text-white">AI Coach</h3>
                                <p className="text-xs text-gray-400">Powered by your gaming data</p>
                            </div>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-2">
                        {messages.map((msg) => (
                            <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
                        ))}
                        {loading && (
                            <div className="flex items-center space-x-2 text-gray-400 text-sm">
                                <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                </div>
                                <span>Thinking...</span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-white/10">
                        <MessageLimit remaining={remainingMessages} total={DAILY_MESSAGE_LIMIT} />
                        <div className="flex space-x-2 mt-2">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                disabled={remainingMessages <= 0 || loading}
                                placeholder={
                                    remainingMessages <= 0
                                        ? 'Daily limit reached'
                                        : 'Ask about your stats...'
                                }
                                className="flex-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 disabled:opacity-50"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || loading || remainingMessages <= 0}
                                className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 text-white disabled:opacity-50"
                            >
                                ➤
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
