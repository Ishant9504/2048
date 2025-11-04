import axios from 'axios'
import { setupCSRF } from './csrf'

// For development with Vite proxy
const isDevelopment = import.meta.env.DEV;
// Use relative URL for development (proxied by Vite)
// or absolute URL for production
const API_BASE = isDevelopment ? '/api' : import.meta.env.VITE_API_BASE;

console.log('API_BASE set to:', API_BASE);

// Configure axios to always send credentials (cookies) with requests
axios.defaults.withCredentials = true;

// Initialize CSRF protection
setupCSRF().catch(err => {
    console.warn('CSRF setup failed:', err);
    console.log('API will still attempt to function without CSRF protection');
});

// Ensure session is created
export const ensureSession = async () => {
    try {
        const res = await axios.get(`${API_BASE}/debug-session/`);
        console.log('Session verified:', res.data);
        return { success: true, data: res.data };
    } catch (err) {
        console.error('Failed to create session:', err);
        return { success: false, error: err.message };
    }
};

// --- NEW AUTHENTICATION FUNCTIONS ---

/**
 * Sends a request to log in the user and establish a session cookie.
 * @param {string} username 
 * @param {string} password 
 */
export const loginUser = async (username, password) => {
    try {
        const url = `${API_BASE}/login/`;
        console.log('Attempting login to:', url);
        const res = await axios.post(
            url,
            { username, password },
            { withCredentials: true } // CRITICAL: Allows session cookie exchange
        );
        console.log('Login successful:', res.data);
        return { data: res.data, success: true };
    } catch (error) {
        console.error('Login error:', error.response?.status, error.response?.data);
        return { 
            error: error.response?.data?.error || 'Login failed. Check credentials.', 
            success: false 
        };
    }
}

/**
 * Sends a request to log out the user and destroy the session cookie.
 */
export const logoutUser = async () => {
    try {
        const res = await axios.post(
            `${API_BASE}/logout/`, // Matches the new path 'api/logout/'
            {}, // No body needed for logout
            { withCredentials: true } // CRITICAL: Ensures the session cookie is destroyed
        );
        return { data: res.data, success: true };
    } catch (error) {
        console.error('Logout error:', error);
        return { 
            error: error.response?.data?.error || 'Logout failed.', 
            success: false 
        };
    }
}

/**
 * Sends a request to register a new user.
 * @param {string} username 
 * @param {string} password 
 */
export const registerUser = async (username, password) => {
    try {
        const url = `${API_BASE}/register/`;
        console.log('Attempting registration to:', url);
        
        // Log the headers being sent
        const csrfToken = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        console.log('CSRF token before request:', csrfToken || 'Not found');
        console.log('Current cookies:', document.cookie);
        
        // Include both withCredentials and explicit headers
        const res = await axios.post(
            url,
            { username, password },
            { 
                withCredentials: true,
                headers: {
                    'X-CSRFToken': csrfToken || '',
                    'Content-Type': 'application/json'
                }
            }
        );
        console.log('Registration successful:', res.data);
        return { data: res.data, success: true };
    } catch (error) {
        console.error('Registration error:', error.response?.status, error.response?.data);
        // Log the detailed error for debugging
        if (error.response) {
            console.error('Error details:', {
                status: error.response.status,
                headers: error.response.headers,
                data: error.response.data
            });
        }
        return {
            error: error.response?.data?.error || 'Registration failed. Please try again.',
            success: false
        };
    }
}

/**
 * Fetches the list of available AI Models. (Now publicly accessible if views.py was updated)
 */
export const fetchAIModels = async () => {
    try {
        // We still use withCredentials: true to send the cookie if it exists
        const res = await axios.get(`${API_BASE}/ai-models/`, { withCredentials: true });
        return { data: res.data, success: true }; 
    } catch (error) {
        return { 
            error: error.response?.data?.error || 'Failed to fetch AI models.', 
            success: false 
        };
    }
}

/**
 * Sends a request to purchase an AI model. (Requires user to be logged in)
 */
export const purchaseAI = async (ai_model_id) => {
    try {
        const res = await axios.post(
            `${API_BASE}/purchase-ai/`,
            { ai_model_id },
            { withCredentials: true } // CRITICAL: Requires valid session cookie
        )
        return { data: res.data, success: true };
    } catch (error) {
        let message;
        switch (error.response?.status) {
            case 403:
                message = "You must be logged in to purchase an AI model.";
                break;
            case 402:
                message = "Not enough points to purchase this AI model.";
                break;
            case 400:
                message = error.response?.data?.error || "Invalid request.";
                break;
            default:
                message = error.response?.data?.error || 'Purchase failed due to an unknown error.';
        }
        return { 
            error: message, 
            success: false 
        };
    }
}
export const getUserAiProfile = async () => {
  try {
    const response = await axios.get(`${API_BASE}/user-ai-profile/`);
    // The backend sends an object like: { equipped_ai: {...}, ai_configs: {...} }
    // We also need to get the list of unlocked AI IDs for the UI.
    const unlockedResponse = await axios.get(`${API_BASE}/ai-models/`); // Re-using the models list endpoint
    
    const unlockedIds = unlockedResponse.data.filter(model => model.unlocked).map(model => model.id);

    return { 
      success: true, 
      data: {
        ...response.data,
        unlocked: unlockedIds, // Add the list of unlocked IDs
      }
    };
  } catch (error) {
    console.error("Failed to fetch user AI profile:", error);
    return { success: false, error: error.response?.data?.error || error.message };
  }
};
/**
 * Saves the user's AI configuration.
 * @param {number} equippedAiId - The ID of the AI model to equip.
 * @param {object} configs - The dictionary of custom slider values for this AI.
 */
export const saveUserAiProfile = async (equippedAiId, configs) => {
  try {
    const payload = {
      equipped_ai_id: equippedAiId,
      configs: configs
    };
    const response = await axios.post(`${API_BASE}/user-ai-profile/`, payload);
    return { success: true, data: response.data };
  } catch (error) {
    console.error("Failed to save user AI profile:", error);
    return { success: false, error: error.response?.data?.error || error.message };
  }
};

export const getLeaderboard = async (mode) => {
    try {
        const response = await axios.get(`${API_BASE}/leaderboard/`, {
            params: {mode}
        })
        // The backend sends the array directly.
        return response.data; 
    } catch (error) {
        console.error(`Error fetching ${mode} leaderboard:`, error);
        throw error;
    }
};
/**
 * Fetches current logged in user information.
 * This is used to check authentication status and get user details.
 */
export const fetchCurrentUser = async () => {
    try {
        console.log('Trying to fetch user from:', `${API_BASE}/user/`);
        const res = await axios.get(`${API_BASE}/user/`, { 
            withCredentials: true,
            // Add timeout to prevent long waits if server is down
            timeout: 5000
        });
        console.log('Current user data:', res.data);
        return res.data;
    } catch (error) {
        if (error.response && error.response.status === 404) {
            console.warn('User endpoint not found (404). Make sure the backend route is correctly set up.');
        } else if (error.response && error.response.status === 401) {
            console.log('User not authenticated (401). This is normal if not logged in.');
        } else {
            console.error('Failed to fetch current user:', error);
        }
        // Return null for any error - the app should handle this as "not authenticated"
        return null;
    }
}

/**
 * Helper function to get the current authenticated user's username.
 * Returns the username if authenticated, null otherwise.
 */
export const getCurrentUser = async () => {
    try {
        const userData = await fetchCurrentUser();
        if (userData && userData.username) {
            return userData.username;
        }
        return null;
    } catch (error) {
        console.error('Error in getCurrentUser:', error);
        return null;
    }
}

export const completeGame = async (score, boardState, mode = 'manual', aiModelId = null) => {
    try {
        console.log('Completing game:', { score, mode });
        const res = await axios.post(
            `${API_BASE}/complete-game/`,
            {
                score,
                board_state: boardState,
                mode,
                ai_model_id: aiModelId
            },
            { withCredentials: true }
        );
        console.log('Game completed successfully:', res.data);
        return {
            success: true,
            data: res.data
        };
    } catch (error) {
        console.error('Error completing game:', error);
        return {
            success: false,
            error: error.response?.data?.error || error.message
        };
    }
};

/**
 * Get current user's statistics
 */
export const getUserStats = async () => {
    try {
        const res = await axios.get(`${API_BASE}/user-stats/`, { 
            withCredentials: true 
        });
        return {
            success: true,
            data: res.data
        };
    } catch (error) {
        console.error('Error fetching user stats:', error);
        return {
            success: false,
            error: error.response?.data?.error || error.message
        };
    }
};

