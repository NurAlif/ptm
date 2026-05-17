import { defineStore } from 'pinia';
import apiClient, { fetchModelConfig, saveModelConfig } from '@/services/api'; // NEW: Import config functions

export const useModelStore = defineStore('model', {
  state: () => ({
    users: [],
    isLoadingUsers: false,
    buildProcessLog: '',
    // 'buildStatus' now tracks the overall state from the status file
    buildStatus: 'not_started', // can be not_started, running, completed, failed
    isStreaming: false, // tracks the active EventSource connection
    error: null,
    eventSource: null, // holds the EventSource instance to be able to close it

    // --- NEW State for Config Editor ---
    currentConfig: '', // Holds the text content of the config
    isLoadingConfig: false,
    isSavingConfig: false,
    configError: null,
    saveSuccess: false, // For showing a temporary success message
    // --- End New State ---
  }),
  actions: {
    async fetchUsers() {
      this.isLoadingUsers = true;
      this.error = null;
      try {
        const response = await apiClient.get('/models/users');
        this.users = response.data;
      } catch (err) {
        this.error = 'Failed to load user list from the main application.';
        console.error(err);
      } finally {
        this.isLoadingUsers = false;
      }
    },

    async checkBuildStatus(userId) {
      if (!userId) {
        this.buildStatus = 'not_started';
        return;
      }
      this.configError = null; // Clear config error on user change
      this.error = null; // Clear build error

      // Don't set isBuilding, just check status
      try {
        const response = await apiClient.get(`/models/build/${userId}/status`);
        this.buildStatus = response.data.status;
        if (response.data.status === 'running') {
          // If a build is already running, start streaming the logs
          this.streamLogsForUser(userId);
        } else {
             // If not running, clear any old logs unless we are *just* loading
             if (!this.isStreaming) {
                this.buildProcessLog = '';
             }
        }
      } catch (err) {
        this.error = 'Failed to check build status.';
        this.buildStatus = 'failed';
        console.error(err);
      }
    },

    async startBuildForUser(userId, buildMode) {
      if (this.buildStatus === 'running') return; // Don't start if already running

      this.error = null;
      this.configError = null;
      this.buildProcessLog = ''; // Clear previous logs
      this.buildStatus = 'running';

      try {
        // MODIFIED: Send buildMode as a query parameter
        await apiClient.post(`/models/build/${userId}?build_mode=${buildMode}`);
        // Once the build is started, immediately connect to the log stream
        this.streamLogsForUser(userId);
      } catch (err) {
        this.error = `Failed to start model build for user ${userId}. Error: ${err.response?.data?.detail || err.message}`;
        this.buildStatus = 'failed';
        console.error(err);
      }
    },

    streamLogsForUser(userId) {
        // If an EventSource is already open, close it before creating a new one
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.isStreaming = true;
        this.buildProcessLog = 'INFO: Connecting to log stream...\n';

        const token = localStorage.getItem('token');
        if (!token) {
          this.error = "Authentication token not found. Cannot stream logs.";
          this.isStreaming = false;
          return;
        }

        // Use the full URL from the apiClient config for the EventSource
        const streamUrl = `${apiClient.defaults.baseURL}/models/build/${userId}/stream?token=${token}`;
        this.eventSource = new EventSource(streamUrl);
        
        this.eventSource.onmessage = (event) => {
          this.buildProcessLog += event.data + '\n';
        };

        this.eventSource.onerror = (err) => {
          // Don't show an error if it's just a normal close
          if (this.isStreaming) { // Only show error if we weren't expecting to close
            this.error = 'Connection to the build stream failed. The process may still be running. You can reload to reconnect.';
            console.error("EventSource failed:", err);
          }
          this.closeStream();
        };

        this.eventSource.addEventListener('close', (event) => {
          console.log("Backend signaled completion:", event.data);
          this.buildProcessLog += 'INFO: Build process finished.\n';
          this.closeStream();
          // Re-check the final status from the status file
          this.checkBuildStatus(userId);
        });
    },

    closeStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isStreaming = false;
    },

    // --- NEW ACTIONS for Config Editor ---
    async fetchModelConfig(userId) {
        if (!userId) return;
        this.isLoadingConfig = true;
        this.configError = null;
        this.currentConfig = '';
        try {
            // Use the new API service function
            const configData = await fetchModelConfig(userId);
            // Assuming the API returns the JSON as an object
            this.currentConfig = JSON.stringify(configData, null, 2); 
        } catch (err) {
             this.configError = `Failed to load model config: ${err.response?.data?.detail || err.message}`;
             console.error("Config fetch error:", err);
        } finally {
            this.isLoadingConfig = false;
        }
    },

    async saveModelConfig(userId, configContent) {
        if (!userId) return;
        this.isSavingConfig = true;
        this.configError = null;
        this.saveSuccess = false;
        
        let configData;
        try {
            // First, validate if the content is valid JSON
            configData = JSON.parse(configContent);
        } catch (parseError) {
             this.configError = `Invalid JSON format: ${parseError.message}`;
             this.isSavingConfig = false;
             return;
        }

        try {
            // Use the new API service function
            // Send the parsed JSON object
            await saveModelConfig(userId, configData); 
            this.saveSuccess = true;
            // Optionally, clear the success message after a few seconds
            setTimeout(() => { this.saveSuccess = false; }, 3000);
        } catch (err) {
             this.configError = `Failed to save model config: ${err.response?.data?.detail || err.message}`;
             console.error("Config save error:", err);
        } finally {
            this.isSavingConfig = false;
        }
    },
    // --- End New Actions ---
  },
});
