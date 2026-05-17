import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Create an Axios instance for the new admin backend.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_ADMIN_API_BASE_URL || 'https://model2.parasyst.com/api', // Use env variable
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token in every request.
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers['Authorization'] = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- User Management Endpoints ---

/**
 * Fetches a list of all non-admin users (students) from the models router.
 */
export const fetchUsers = async () => {
    try {
        const response = await apiClient.get('/models/users');
        return response.data;
    } catch (error) {
        console.error("Error fetching students:", error);
        throw error;
    }
};

// --- Model Build Endpoints ---

/**
 * Starts the model build process for a user.
 */
export const startBuildForUser = async (userId, buildMode) => {
     try {
        await apiClient.post(`/models/build/${userId}?build_mode=${buildMode}`);
    } catch (error) {
        console.error(`Error starting build for user ${userId}:`, error);
        throw error;
    }
};

/**
 * Checks the build status for a user.
 */
export const checkBuildStatus = async (userId) => {
    try {
        const response = await apiClient.get(`/models/build/${userId}/status`);
        return response.data;
    } catch (error) {
        console.error(`Error checking build status for user ${userId}:`, error);
        throw error;
    }
};

// --- Model Config Endpoints ---

/**
 * Fetches the model build parameters for a specific user.
 */
export const fetchModelConfig = async (userId) => {
    try {
        const response = await apiClient.get(`/models/build/${userId}/config`);
        return response.data; // Returns the config JSON
    } catch (error) {
        console.error(`Error fetching model config for user ${userId}:`, error);
        throw error;
    }
};

/**
 * Saves/updates the model build parameters for a specific user.
 */
export const saveModelConfig = async (userId, configData) => {
    try {
        const response = await apiClient.post(`/models/build/${userId}/config`, configData);
        return response.data; // Returns success message
    } catch (error) {
        console.error(`Error saving model config for user ${userId}:`, error);
        throw error;
    }
};



export default apiClient;