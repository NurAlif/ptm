<template>
  <div class="space-y-8 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-800">
      <div>
        <h2 class="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">Inspect Knowledge Model</h2>
        <p class="text-slate-400 mt-2 text-sm max-w-2xl">
          View and interact with the generated knowledge graph models.
        </p>
      </div>
      <div class="mt-4 md:mt-0 flex items-center space-x-2">
        <span class="h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
        <span class="text-xs text-indigo-400 font-semibold uppercase tracking-wider font-mono">Interactive Explorer</span>
      </div>
    </div>
    
    <!-- Info Card -->
    <div class="bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl p-8 rounded-2xl shadow-xl space-y-6">
      <div class="flex items-center space-x-3 pb-4 border-b border-slate-800">
        <svg class="h-6 w-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="font-bold text-lg text-slate-200">Knowledge Graph Explorer</h3>
      </div>
      
      <p class="text-slate-400 text-sm leading-relaxed max-w-3xl">
        The graph explorer application must be opened in a new tab to function correctly
        due to browser security policies. Once opened, you will be able to search nodes, filter levels, 
        and traverse semantic knowledge structures in real-time.
      </p>
      
      <div class="pt-2">
        <a
          :href="graphViewerUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center px-6 py-3 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-[0_0_12px_rgba(99,102,241,0.4)] hover:shadow-[0_0_20px_rgba(99,102,241,0.6)] focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all duration-300"
        >
          <!-- Icon for "open in new tab" -->
          <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
            <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
          </svg>
          Open Model Inspector
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import apiClient from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

const graphViewerUrl = ref('');

// REMOVED: onIframeLoad is no longer needed
// const onIframeLoad = () => {
//     console.log("Graph viewer iframe loaded successfully.");
// }

// FIX: Construct the URL to the graph viewer, including the API prefix
// and the auth token as a query parameter for the new tab.
const authStore = useAuthStore();
const baseUrl = apiClient.defaults.baseURL; // This now correctly points to http://.../api
const token = authStore.token;
graphViewerUrl.value = `${baseUrl}/models/graph-viewer?token=${token}`;

</script>
