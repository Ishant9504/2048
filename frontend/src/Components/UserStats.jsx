import { useState, useEffect } from "react";
import { getUserStats } from "../api/api";

export default function UserStats({ partition = "stats" }) {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadStats = async () => {
        try {
            const result = await getUserStats();
            if (result.success) setStats(result.data);
        } catch (err) {
            console.error("Failed to load user stats:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadStats();

        const handleGameCompleted = () => {
            console.log("Game completed event received — refreshing stats");
            loadStats();
        };

        window.addEventListener("game-completed", handleGameCompleted);
        return () => window.removeEventListener("game-completed", handleGameCompleted);
    }, []);

    if (loading) {
        return (
            <div className="bg-white/10 text-gray-300 rounded-xl p-6 border border-slate-700/40">
                <h3 className="text-lg font-semibold mb-3">Your Stats</h3>
                <p>Loading...</p>
            </div>
        );
    }

    if (!stats) return null;

    // ----------------------------
    // Partition = "stats" (numerical)
    // ----------------------------
    if (partition === "stats") {
        return (
            <div className="bg-slate-800/60 backdrop-blur-md border border-slate-700/40 rounded-2xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-200 mb-4">Your Stats</h3>

                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-500/10 p-4 rounded-lg border border-blue-500/20">
                        <p className="text-sm text-blue-400 font-semibold">Total Points</p>
                        <p className="text-2xl font-bold text-blue-300">{stats.points}</p>
                    </div>

                    <div className="bg-yellow-500/10 p-4 rounded-lg border border-yellow-500/20">
                        <p className="text-sm text-yellow-400 font-semibold">High Score</p>
                        <p className="text-2xl font-bold text-yellow-300">{stats.high_score}</p>
                    </div>

                    <div className="bg-green-500/10 p-4 rounded-lg border border-green-500/20">
                        <p className="text-sm text-green-400 font-semibold">Games Played</p>
                        <p className="text-2xl font-bold text-green-300">{stats.games_played}</p>
                    </div>

                    <div className="bg-purple-500/10 p-4 rounded-lg border border-purple-500/20">
                        <p className="text-sm text-purple-400 font-semibold">Avg Score</p>
                        <p className="text-2xl font-bold text-purple-300">{stats.average_score}</p>
                    </div>
                </div>
            </div>
        );
    }

    // ----------------------------
    // Partition = "matches" (recent games)
    // ----------------------------
    if (partition === "matches") {
        return (
            <div className="bg-slate-800/60 backdrop-blur-md border border-slate-700/40 rounded-2xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-200 mb-4">Recent Matches</h3>

                {stats.recent_games?.length > 0 ? (
                    <div className="space-y-2">
                        {stats.recent_games.map((game, idx) => (
                            <div key={idx} className="flex justify-between items-center bg-slate-700/40 rounded-lg px-3 py-2">
                                <span className="text-gray-300 text-sm">Score: {game.score}</span>
                                <span className="text-gray-500 text-xs">
                                    {new Date(game.date).toLocaleDateString()}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-400 text-sm">No recent games found.</p>
                )}
            </div>
        );
    }

    return null;
}
