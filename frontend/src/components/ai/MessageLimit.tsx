import React from 'react';

interface MessageLimitProps {
    remaining: number;
    total: number;
}

export const MessageLimit: React.FC<MessageLimitProps> = ({ remaining, total }) => {
    const percentage = (remaining / total) * 100;

    return (
        <div className="flex items-center space-x-2 text-xs">
            <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all ${remaining === 0
                            ? 'bg-red-500'
                            : remaining <= 2
                                ? 'bg-yellow-500'
                                : 'bg-gradient-to-r from-purple-500 to-cyan-500'
                        }`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
            <span className={`${remaining === 0 ? 'text-red-400' : 'text-gray-500'}`}>
                {remaining}/{total} left
            </span>
        </div>
    );
};
