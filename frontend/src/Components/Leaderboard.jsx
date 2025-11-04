import { useEffect, useState } from "react";
import { getLeaderboard } from "../api/api";

export default function Leaderboard() {
    const [leaders, setLeaders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    const modes = ['total', 'human', 'ai'];
    const modeDetails = {
        total: { label: 'Total Score', color: 'text-yellow-400' },
        human: { label: 'Human Score', color: 'text-blue-400' },
        ai: { label: 'AI Score', color: 'text-purple-400' }
    };
    const [mode, setMode] = useState('total'); 

    const fetchLeaderboard = async (currentMode) => {
        // if (isManualRefresh) {
        //     setRefreshing(true);
        // } else {
        //     setLoading(true);
        // }
        setError(null);
        try {
            const data = await getLeaderboard(currentMode);
            if (Array.isArray(data)) {
                setLeaders(data);
            } else {
                // This is a safety net in case the API returns something unexpected
                console.error("API did not return an array for leaderboard:", data);
                setLeaders([]); 
            }
        } catch (err) {
            setError('Failed to load leaderboard.');
            console.error(err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };
    const handleManualRefresh = () => {
        fetchLeaderboard(true);
    };

    const handleModeToggle = () => {
        const currentIndex = modes.indexOf(mode);
        const nextIndex = (currentIndex + 1) % modes.length;
        setMode(modes[nextIndex]);
    };

    useEffect(() => {
        fetchLeaderboard(mode);

        const handleGameCompleted = () => {
            console.log("Leaderboard: 'game-completed' event received. Refreshing data...");
            setTimeout(() => {
                fetchLeaderboard(mode);
            }, 1000); // 1-second delay
        };
        window.addEventListener('game-completed', handleGameCompleted);

        // Cleanup: remove the event listener when the component unmounts
        return () => {
            window.removeEventListener('game-completed', handleGameCompleted);
        };
        // const interval = setInterval(fetchLeaderboard, 60000); // Refresh every 60 seconds
        // return () => clearInterval(interval);
    }, [mode]);

    const renderContent = () => {
        if (loading && !refreshing) {
            return (
                <div className="flex items-center justify-center p-8 text-gray-400">
                    <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Loading...</span>
                </div>
            );
        }

        if (error) {
            return (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg">
                    <strong className="font-bold">Error: </strong>
                    <span>{error}</span>
                </div>
            );
        }
        
        if (leaders.length === 0) {
            return (
                <div className="bg-blue-500/10 border border-blue-500/30 text-blue-400 px-4 py-3 rounded-lg text-center">
                    <span>No games yet. Be the first!</span>
                </div>
            );
        }

        const getRankIcon = (rank) => {
            if (rank === 1) return '🥇';
            if (rank === 2) return '🥈';
            if (rank === 3) return '🥉';
            return null;
        };

        return (
            <div className="space-y-2">
                {leaders.map((entry, idx) => {
                    const rank = entry.rank || idx + 1;
                    const isTop3 = rank <= 3;

                    let displayScore = 0;
                    if (mode === 'human') displayScore = entry.human_score;
                    else if (mode === 'ai') displayScore = entry.ai_score;
                    else displayScore = entry.total_score;

                    
                    return (
                        <div 
                            key={idx} 
                            className={`group p-3 rounded-lg transition-all ${
                                rank === 1 
                                    ? 'bg-gradient-to-r from-yellow-500/20 to-amber-500/20 border border-yellow-500/30' 
                                    : rank === 2
                                    ? 'bg-gradient-to-r from-slate-400/20 to-gray-400/20 border border-slate-400/30'
                                    : rank === 3
                                    ? 'bg-gradient-to-r from-orange-500/20 to-amber-600/20 border border-orange-500/30'
                                    : 'bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800/60'
                            }`}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <div className={`flex-shrink-0 w-8 text-center font-bold ${
                                        isTop3 ? 'text-xl' : 'text-gray-400'
                                    }`}>
                                        {getRankIcon(rank) || `#${rank}`}
                                    </div>
                                    
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-gray-200 truncate">
                                            {entry.username}
                                        </div>
                                        {entry.games_played && (
                                            <div className="text-xs text-gray-500">
                                                {entry.games_played} games
                                            </div>
                                        )}
                                    </div>
                                </div>
                                
                                <div className="relative text-right flex-shrink-0 w-24">
                                    {/* --- MAIN SCORE DISPLAY --- */}
                                    {/* Shows the score relevant to the current mode */}
                                    <div className={`font-bold text-lg transition-opacity duration-300 ${mode === 'total' ? 'group-hover:opacity-0' : ''} ${modeDetails[mode].color}`}>
                                        {displayScore?.toLocaleString() || 0}
                                    </div>
                                    
                                    {/* --- HOVER BREAKDOWN --- */}
                                    {/* Only appears when in 'total' mode */}
                                    {mode === 'total' && (
                                        <div className="absolute top-0 right-0 h-full flex items-center justify-end gap-1 transition-opacity duration-300 opacity-0 group-hover:opacity-100">
                                            <span className="text-sm font-semibold text-blue-400">{entry.human_score}</span>
                                            <span className="text-xs text-gray-400">+</span>
                                            <span className="text-sm font-semibold text-purple-400">{entry.ai_score}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="bg-slate-800/40 backdrop-blur-sm rounded-xl p-5 border border-slate-700/50 h-full flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-200">Top Players</h3>
                <div className="flex items-center p-1 bg-slate-900/50 rounded-lg">         
                    <button
                        onClick={handleModeToggle}
                        className="px-3 py-1 text-sm font-medium rounded-lg bg-slate-700 hover:bg-slate-600 transition-all text-white flex items-center gap-2"
                    >
                    <span className={`font-semibold ${modeDetails[mode].color}`}>
                        {modeDetails[mode].label}
                    </span>
                    <span className="text-gray-400">⇄</span>
                    </button>
                </div>
                <button 
                    onClick={handleManualRefresh}
                    className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 disabled:opacity-50 transition-all"
                    disabled={loading || refreshing}
                >
                    {refreshing ? (
                        <>
                            <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>Refreshing</span>
                        </>
                    ) : (
                        <>
                            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span>Refresh</span>
                        </>
                    )}
                </button>
            </div>
            
            <div className="flex-1 overflow-y-auto">
                {renderContent()}
            </div>
        </div>
    );
}