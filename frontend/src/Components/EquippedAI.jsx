// In frontend/src/Components/EquippedAI.jsx

import { useState, useEffect } from 'react';
import { getUserAiProfile } from '../api/api'; 

export default function EquippedAI({ onOpenDrawer, onStartAI }) {
    const [aiProfile, setAiProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [numMoves, setNumMoves] = useState(5);

    const loadProfile = async () => {
        setLoading(true);
        const result = await getUserAiProfile();
        if (result.success) {
            setAiProfile(result.data);
        }
        setLoading(false);
    };

    useEffect(() => {
        loadProfile();
        const handleConfigChange = () => {
            console.log("AI config changed, reloading profile...");
            loadProfile();
        };
        window.addEventListener('ai-config-changed', handleConfigChange);
        return () => window.removeEventListener('ai-config-changed', handleConfigChange);
    }, []);

    if (loading) return <p>Loading AI...</p>;

    const equippedAI = aiProfile?.equipped_ai;
    const currentConfig = equippedAI ? aiProfile?.ai_configs?.[equippedAI.id] : null;
    
    return (
        <div className="bg-slate-800/60 backdrop-blur-md border border-slate-700/40 rounded-2xl shadow-lg p-6 h-full flex flex-col">
            
            {equippedAI ? (
                <div className="flex flex-col h-full">
                    {/* AI Info - Fixed Height */}
                    <div className="mb-4">
                        <h3 className="text-lg font-bold text-purple-400 mb-1.5">{equippedAI.name}</h3>
                        <p className="text-sm text-gray-400 line-clamp-2 leading-snug">{equippedAI.description}</p>
                    </div>

                    {/* Configuration Display - Flex Grow */}
                    <div className="flex-1 min-h-0 mb-4">
                        {currentConfig && Object.keys(currentConfig).length > 0 ? (
                            <div className="bg-slate-900/40 rounded-xl p-3 border border-slate-700/30 h-full overflow-y-auto">
                                <div className="space-y-2">
                                    {Object.entries(currentConfig).map(([key, value]) => (
                                        <div key={key} className="flex justify-between items-center text-sm">
                                            <span className="text-gray-400">
                                                {equippedAI.tunable_params[key]?.label || key.replace(/_/g, ' ')}:
                                            </span>
                                            <span className="font-mono font-semibold text-purple-300">
                                                {typeof value === 'number' ? Number(value.toFixed(2)) : value}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex items-center justify-center">
                                <p className="text-xs text-gray-500 italic">No configuration set</p>
                            </div>
                        )}
                    </div>
                    
                    {/* Actions Area - Fixed Height */}
                    <div className="flex gap-12 h-16">
                        {/* Moves Counter - Crystalline Design */}
                        <div className="relative group w-20 flex-shrink-0">
                            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-lg blur-sm group-hover:blur-md transition-all"></div>
                            <div className="relative h-full bg-slate-900/60 backdrop-blur-xl border border-slate-600/50 rounded-lg flex flex-col items-center justify-center shadow-lg">
                                <label className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide mb-1">Moves</label>
                                <input 
                                    type="number"
                                    value={numMoves}
                                    onChange={(e) => setNumMoves(Math.max(1, Math.min(250, parseInt(e.target.value, 10) || 1)))}
                                    className="w-12 text-base font-bold bg-transparent text-center text-white focus:outline-none focus:text-purple-300 transition-colors"
                                    min="1" 
                                    max="250"
                                />
                            </div>
                        </div>

                        {/* Buttons - Crystalline Design */}
                        <div className="flex-1 flex flex-col gap-2">
                            {/* Configure Button */}
                            <div className="relative group flex-1">
                                <div className="absolute inset-0 bg-gradient-to-r from-slate-500/20 to-slate-400/20 rounded-lg blur-sm group-hover:blur transition-all"></div>
                                <button 
                                    onClick={onOpenDrawer}
                                    className="relative w-full h-full bg-slate-800/70 hover:bg-slate-700/70 backdrop-blur-xl border border-slate-600/50 rounded-lg text-slate-200 hover:text-white text-sm font-semibold transition-all duration-200 shadow-lg hover:shadow-slate-500/20 hover:scale-[1.02] active:scale-[0.98]"
                                >
                                    Configure
                                </button>
                            </div>
                            
                            {/* Get Moves Button */}
                            <div className="relative group flex-1">
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-lg blur-sm group-hover:blur-md transition-all"></div>
                                <button
                                    onClick={() => onStartAI({ num_moves: numMoves })}
                                    className="relative w-full h-full bg-gradient-to-r from-blue-600/10 to-purple-600/10 hover:from-blue-600/30 hover:to-purple-600/30 backdrop-blur-xl border border-blue-400/50 rounded-lg text-blue-100 hover:text-white text-sm font-bold transition-all duration-200 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98]"
                                >
                                    Get Moves
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="flex-1 flex flex-col justify-center items-center">
                    <p className="text-gray-400 mb-4 text-sm">No AI equipped.</p>
                    <div className="relative group">
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-lg blur-sm group-hover:blur-md transition-all"></div>
                        <button 
                            onClick={onOpenDrawer}
                            className="relative px-6 py-3 bg-slate-800/70 backdrop-blur-xl border border-slate-600/50 rounded-lg text-slate-200 hover:text-white text-sm font-semibold transition-all duration-200 shadow-lg hover:scale-105 active:scale-95"
                        >
                            Select & Configure AI
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}