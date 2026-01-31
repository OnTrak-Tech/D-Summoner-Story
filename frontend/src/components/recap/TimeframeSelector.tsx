import React from 'react';

export type Timeframe = 'all-time' | 'month' | 'season';

interface TimeframeSelectorProps {
    selected: Timeframe;
    onChange: (timeframe: Timeframe) => void;
}

const timeframes: { id: Timeframe; label: string }[] = [
    { id: 'all-time', label: 'All-Time' },
    { id: 'month', label: 'This Month' },
    { id: 'season', label: 'This Season' },
];

export const TimeframeSelector: React.FC<TimeframeSelectorProps> = ({
    selected,
    onChange,
}) => {
    return (
        <div className="flex space-x-2 p-1 bg-white/5 rounded-xl">
            {timeframes.map((tf) => (
                <button
                    key={tf.id}
                    onClick={() => onChange(tf.id)}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-all ${selected === tf.id
                            ? 'bg-gradient-to-r from-purple-600 to-cyan-600 text-white'
                            : 'text-gray-400 hover:text-white'
                        }`}
                >
                    {tf.label}
                </button>
            ))}
        </div>
    );
};
