import React from 'react';

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, content }) => {
    const isUser = role === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
            <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl ${isUser
                        ? 'bg-gradient-to-r from-purple-600 to-cyan-600 text-white'
                        : 'bg-white/10 text-gray-200'
                    }`}
            >
                {!isUser && (
                    <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm">🤖</span>
                        <span className="text-xs font-medium text-purple-400">AI Coach</span>
                    </div>
                )}
                <p className="text-sm whitespace-pre-wrap">{content}</p>
            </div>
        </div>
    );
};
