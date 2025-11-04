import { useState, useRef, useEffect } from 'react';

export default function Slider({ label, value, min, max, step, onChange }) {
    const trackRef = useRef(null);
    const [isDragging, setIsDragging] = useState(false);
    
    const percentage = ((value - min) / (max - min)) * 100;

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging || !trackRef.current) return;
            
            const trackRect = trackRef.current.getBoundingClientRect();
            const relativeX = Math.max(0, Math.min(e.clientX - trackRect.left, trackRect.width));
            const percent = relativeX / trackRect.width;
            let newValue = min + percent * (max - min);
            newValue = Math.round(newValue / step) * step;
            newValue = Math.max(min, Math.min(newValue, max));
            onChange(newValue);
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, min, max, step, onChange]);

    const handleIncrement = () => {
        const newValue = Math.min(max, value + step);
        onChange(newValue);
    };

    const handleDecrement = () => {
        const newValue = Math.max(min, value - step);
        onChange(newValue);
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-300">{label}</label>
                <span className="font-mono text-base font-semibold text-purple-300">
                    {parseFloat(value).toFixed(2)}
                </span>
            </div>
            
            <div className="flex items-center gap-2">
                {/* Minus Button */}
                <button
                    onClick={handleDecrement}
                    disabled={value <= min}
                    className="w-8 h-8 bg-slate-800/70 backdrop-blur-xl border border-slate-600/50 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/70 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center font-bold text-lg hover:scale-105 active:scale-95"
                >
                    −
                </button>

                {/* Slider Track */}
                <div
                    ref={trackRef}
                    onMouseDown={() => setIsDragging(true)}
                    className="relative flex-1 h-2 bg-slate-700 rounded-full cursor-pointer"
                >
                    {/* The filled part of the track */}
                    <div
                        className="absolute h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                        style={{ width: `${percentage}%` }}
                    />
                    {/* The draggable thumb */}
                    <div
                        className="absolute top-1/2 w-5 h-5 bg-white rounded-full shadow-lg border-2 border-slate-900 transform -translate-y-1/2 -translate-x-1/2 transition-transform hover:scale-110"
                        style={{ left: `${percentage}%` }}
                    />
                </div>

                {/* Plus Button */}
                <button
                    onClick={handleIncrement}
                    disabled={value >= max}
                    className="w-8 h-8 bg-slate-800/70 backdrop-blur-xl border border-slate-600/50 rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/70 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center font-bold text-lg hover:scale-105 active:scale-95"
                >
                    +
                </button>
            </div>
        </div>
    );
}