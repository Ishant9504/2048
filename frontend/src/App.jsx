import { useState, useEffect, useRef } from "react";
import GameBoard from "./Components/GameBoard.jsx";
import EquippedAI from "./Components/EquippedAI.jsx";
import AIDrawer from "./Components/AIDrawer.jsx";
import Leaderboard from "./Components/Leaderboard.jsx";
import UserStats from "./Components/UserStats.jsx";
import Login from "./Components/Login.jsx";
import Register from "./Components/Register.jsx";
import { logoutUser, fetchCurrentUser } from "./api/api.js";

const GAME_STATE_STORAGE_KEY = "gameBoardState";

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentGameScore, setCurrentGameScore] = useState(0);
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const [gameConnection, setGameConnection] = useState(false); // NEW: Track WebSocket connection

  const authStateRef = useRef({ authenticated: false, username: null });
  const GAME_ENDPOINT_ID = "game_instance";
  const gameBoardRef = useRef(null);
  const authCheckIntervalRef = useRef(null);

  const triggerAIHandler = ({ num_moves }) => {
    console.log(
      "App.jsx: AI handler triggered. Calling GameBoard's startAI function."
    );
    if (gameBoardRef.current) {
      gameBoardRef.current.startAI({ num_moves });
    } else {
      console.error("Could not find GameBoard component reference.");
    }
  };

  useEffect(() => {
    console.log(
      "App.jsx: Setting up authentication monitoring (should see this ONCE)"
    );

    let mounted = true;

    const checkAuth = async () => {
      if (!mounted) return;

      try {
        const user = await fetchCurrentUser();

        if (!mounted) return;

        const wasAuthenticated = authStateRef.current.authenticated;
        const prevUsername = authStateRef.current.username;

        if (user && user.username) {
          console.log("User authenticated:", user.username);
          setAuthenticated(true);
          setCurrentUser(user);

          authStateRef.current = {
            authenticated: true,
            username: user.username,
          };

          // Only reconnect if this is a NEW login (not just a periodic check)
          if (!wasAuthenticated || prevUsername !== user.username) {
            console.log("Auth state changed - triggering reconnect");
            setTimeout(() => {
              if (mounted && gameBoardRef.current) {
                gameBoardRef.current.reconnect();
              }
            }, 500);
          }
        } else {
          console.log("No authenticated user found");
          setAuthenticated(false);
          setCurrentUser(null);

          authStateRef.current = { authenticated: false, username: null };

          // Only reconnect if user WAS logged in before (logout happened)
          if (wasAuthenticated) {
            console.log("Logout detected - triggering WebSocket reconnect.");
            setTimeout(() => {
              if (mounted && gameBoardRef.current) {
                gameBoardRef.current.reconnect();
              }
            }, 500);
          }
        }
      } catch (error) {
        if (!mounted) return;

        console.error("Authentication check failed:", error);
        setAuthenticated(false);
        setCurrentUser(null);
        authStateRef.current = { authenticated: false, username: null };
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Initial auth check
    checkAuth();

    // Periodic auth check every 30 seconds
    // This helps detect session expiration
    authCheckIntervalRef.current = setInterval(() => {
      if (mounted) {
        checkAuth();
      }
    }, 30000);

    return () => {
      console.log("App.jsx: Cleaning up auth monitoring");
      mounted = false;
      if (authCheckIntervalRef.current) {
        clearInterval(authCheckIntervalRef.current);
        authCheckIntervalRef.current = null;
      }
    };
  }, []); // Empty array is correct - we want this to run once

  const handleAuthSuccess = (userData) => {
    console.log("Auth success handler called with:", userData);
    setAuthenticated(true);
    setCurrentUser(userData);
    authStateRef.current = { authenticated: true, username: userData.username };

    // Trigger WebSocket reconnect after successful login
    setTimeout(() => {
      if (gameBoardRef.current) {
        gameBoardRef.current.reconnect();
      }
    }, 500);
  };

  const handleLogout = async () => {
    try {
      console.log("Logging out user...");
      await logoutUser();
      console.log("Logout successful, clearing user state");

      setAuthenticated(false);
      setCurrentUser(null);
      setCurrentGameScore(0);
      authStateRef.current = { authenticated: false, username: null };

      // Trigger WebSocket reconnect after logout
      setTimeout(() => {
        if (gameBoardRef.current) {
          gameBoardRef.current.reconnect();
        }
      }, 500);

      // Verify logout after a short delay
      setTimeout(async () => {
        try {
          console.log("Post-logout authentication check");
          const user = await fetchCurrentUser();
          if (user && user.username) {
            console.warn("User still authenticated after logout!");
            setAuthenticated(true);
            setCurrentUser(user);
            authStateRef.current = {
              authenticated: true,
              username: user.username,
            };
          } else {
            console.log("User confirmed logged out");
          }
        } catch (error) {
          console.error("Post-logout auth check failed:", error);
        }
      }, 1000);
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  const handleScoreUpdate = (newScore) => {
    setCurrentGameScore(newScore);
  };

  const handleConnectionChange = (isConnected) => {
    setGameConnection(isConnected);
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-gray-900 via-slate-900 to-gray-800 flex items-center justify-center">
        <div className="text-gray-300 text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-gray-900 via-slate-900 to-gray-800 overflow-hidden">
      {!authenticated ? (
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-full max-w-md bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 shadow-2xl">
            <div className="mb-6 flex gap-2 p-1 bg-slate-900/50 rounded-xl">
              <button
                onClick={() => setShowRegister(false)}
                className={`flex-1 px-6 py-2.5 rounded-lg font-medium transition-all ${
                  !showRegister
                    ? "bg-blue-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setShowRegister(true)}
                className={`flex-1 px-6 py-2.5 rounded-lg font-medium transition-all ${
                  showRegister
                    ? "bg-emerald-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Register
              </button>
            </div>

            {showRegister ? (
              <Register onSuccess={handleAuthSuccess} />
            ) : (
              <Login onSuccess={handleAuthSuccess} />
            )}
          </div>
        </div>
      ) : (
        <div className="h-screen flex flex-col px-4 py-1 pb-4">
          {/* Header - Compact and polished */}
          <div className="flex items-center justify-between mb-6 px-6 py-3 bg-slate-800/30 backdrop-blur-sm rounded-xl border border-slate-700/30 shadow-lg">
            <div className="flex items-center gap-6">
              <div className="text-gray-200">
                <span className="text-xs text-gray-400 uppercase tracking-wide">
                  Welcome back,
                </span>
                <div className="text-lg font-bold text-blue-400">
                  {currentUser?.username || "Player"}
                </div>
              </div>

              <div className="h-8 w-px bg-slate-600/50"></div>

              <div className="flex gap-3">
                {currentUser?.points !== undefined && (
                  <div className="px-4 py-1.5 bg-gradient-to-br from-amber-500/15 to-yellow-500/15 border border-amber-500/20 rounded-lg backdrop-blur-sm">
                    <div className="text-[10px] text-amber-400/60 font-medium uppercase tracking-wider">
                      Balance
                    </div>
                    <div className="text-base font-bold text-amber-400">
                      {currentUser.points}
                    </div>
                  </div>
                )}

                {/* <div className="px-4 py-1.5 bg-gradient-to-br from-blue-500/15 to-cyan-500/15 border border-blue-500/20 rounded-lg backdrop-blur-sm">
                                    <div className="text-[10px] text-blue-400/60 font-medium uppercase tracking-wider">Score</div>
                                    <div className="text-base font-bold text-blue-400">{currentGameScore}</div>
                                </div> */}

                {/* NEW: Connection Status in Navbar */}
                <div className="px-4 py-1.5 bg-gradient-to-br from-slate-500/15 to-slate-600/15 border border-slate-500/20 rounded-lg backdrop-blur-sm">
                  <div className="text-[10px] text-slate-400/60 font-medium uppercase tracking-wider">
                    Game
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        gameConnection
                          ? "bg-green-400 animate-pulse"
                          : "bg-red-400"
                      }`}
                    ></div>
                    <div
                      className={`text-sm font-bold ${
                        gameConnection ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {gameConnection ? "Live" : "Offline"}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="px-5 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 hover:text-red-300 rounded-lg font-medium transition-all border border-red-500/20 backdrop-blur-sm"
            >
              Logout
            </button>
          </div>

          {/* Main Content Grid - Single screen, no scrolling */}
          <div className="flex-1 grid grid-cols-12 gap-1 min-h-0">
            {/* Left Column - AI & Recent Matches */}
            <div className="col-span-3 flex flex-col gap-5 min-h-0">
              {/* AI Competitors - Top Left */}
              <div className="flex-1 min-h-0">
                <EquippedAI
                  onOpenDrawer={() => setIsAiDrawerOpen(true)}
                  onStartAI={triggerAIHandler}
                />
              </div>

              {/* Recent Matches - Bottom Left */}
              <div className="h-[45%]">
                <UserStats partition="matches" />
              </div>
            </div>

            {/* Center Column - Game Board */}
            <div className="col-span-6 flex items-center justify-center min-h-0">
              <div className="w-full h-full flex justify-center ">
                <GameBoard
                  ref={gameBoardRef}
                  gameId={GAME_ENDPOINT_ID}
                  onScoreUpdate={handleScoreUpdate}
                  onConnectionChange={handleConnectionChange}
                  username={currentUser?.username}
                />
              </div>
            </div>

            {/* Right Column - Leaderboard & User Stats */}
            <div className="col-span-3 flex flex-col gap-5 min-h-0">
              {/* Leaderboard - Top Right */}
              <div className="flex-1 min-h-0">
                <Leaderboard />
              </div>

              {/* User Stats - Bottom Right */}
              <div className="h-[45%]">
                <UserStats partition="stats" />
              </div>
            </div>
          </div>
          <AIDrawer
            isOpen={isAiDrawerOpen}
            onClose={() => setIsAiDrawerOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
