import { useEffect, useState } from "react";
import { fetchAIModels, purchaseAI, saveUserAiProfile, getUserAiProfile } from "../api/api";
// We will create this component in the next step
import AIProfileView from './AIProfileView'; 

export default function AIDrawer({ isOpen, onClose }) {
    const [groupedModels, setGroupedModels] = useState({});
    const [userProfile, setUserProfile] = useState({ unlocked: [], configs: {} });
    const [selectedAI, setSelectedAI] = useState(null); // This will hold the AI for the "profile view"
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen) {
            const loadData = async () => {
                setLoading(true);
                const modelsResult = await fetchAIModels();
                const profileResult = await getUserAiProfile();

                if (modelsResult.success && profileResult.success) {
                    // --- GROUPING LOGIC ---
                    const groups = {};
                    for (const model of modelsResult.data) {
                        if (!groups[model.agent_class]) {
                            groups[model.agent_class] = [];
                        }
                        groups[model.agent_class].push(model);
                    }
                    setGroupedModels(groups);
                    setUserProfile(profileResult.data);
                }
                setLoading(false);
            };
            loadData();
        }
    }, [isOpen]);

    // When the user clicks "View", we set the selected AI to open the profile view
    const handleViewProfile = (ai) => {
        setSelectedAI(ai);
    };

    // When the user closes the profile view, we clear the selection
    const handleBackToList = () => {
        setSelectedAI(null);
    };
    
    // This function will be passed down to AIProfileView
    const handlePurchaseSuccess = (purchasedId) => {
        setUserProfile(prev => ({
            ...prev,
            unlocked: [...prev.unlocked, purchasedId]
        }));
    };


    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end" onClick={onClose}>
            <div 
                className="w-1/3 h-full bg-slate-900 shadow-2xl p-8 overflow-y-auto" 
                onClick={(e) => e.stopPropagation()} // Prevents clicks inside from closing the drawer
            >
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white">&times;</button>
                
                {selectedAI ? (
                    <AIProfileView 
                        ai={selectedAI}
                        userProfile={userProfile}
                        onBack={handleBackToList}
                        onPurchaseSuccess={handlePurchaseSuccess}
                        onSetConfig={onClose} 
                    />
                ) : (
                    // --- MAIN AI LISTING ---
                    <>
                        <h2 className="text-2xl font-bold text-white mb-6">Select AI Model</h2>
                        {loading ? <p>Loading...</p> : (
                            <div className="space-y-8">
                                {Object.entries(groupedModels).map(([agentClass, models]) => (
                                    <div key={agentClass}>
                                        <h3 className="text-lg font-semibold text-purple-400 border-b-2 border-purple-800/50 pb-2 mb-4">
                                            {agentClass}
                                        </h3>
                                        <div className="space-y-3">
                                            {models.map(ai => (
                                                <div key={ai.id} className="bg-slate-800 p-4 rounded-lg flex justify-between items-center">
                                                    <div>
                                                        <strong className="text-white">{ai.name}</strong>
                                                        <p className="text-sm text-gray-400">{ai.cost} pts</p>
                                                    </div>
                                                    <button 
                                                        onClick={() => handleViewProfile(ai)}
                                                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-gray-300 rounded-lg font-medium transition"
                                                    >
                                                        View
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}