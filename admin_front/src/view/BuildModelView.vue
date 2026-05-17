<template>
  <div class="space-y-8 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-800">
      <div>
        <h2 class="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">Build Knowledge Model</h2>
        <p class="text-slate-400 mt-2 text-sm max-w-2xl">
          Trigger and monitor the background construction of cognitive hierarchical knowledge models from raw student journal entries.
        </p>
      </div>
      <div class="mt-4 md:mt-0 flex items-center space-x-2">
        <span class="h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
        <span class="text-xs text-indigo-400 font-semibold uppercase tracking-wider font-mono">Cognitive Pipeline</span>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Selection and Trigger -->
      <div class="lg:col-span-1 space-y-6">
        <div class="bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl p-6 rounded-2xl shadow-xl space-y-6">
          <div class="flex items-center space-x-2 pb-4 border-b border-slate-850">
            <svg class="h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h3 class="font-bold text-slate-200">Execution Config</h3>
          </div>

          <!-- User Selection -->
          <div class="space-y-2">
            <label for="user-select" class="block text-xs font-semibold text-slate-400 uppercase tracking-widest">Select Student</label>
            <div class="relative">
              <select
                id="user-select"
                v-model="selectedUserId"
                :disabled="modelStore.isLoadingUsers || modelStore.buildStatus === 'running'"
                class="block w-full pl-3 pr-10 py-3 bg-slate-950 border border-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm rounded-xl text-slate-200 disabled:opacity-50 transition-all duration-200 appearance-none"
              >
                <option :value="null" disabled>
                  {{ modelStore.isLoadingUsers ? 'Loading users...' : 'Please select a student' }}
                </option>
                <option v-for="user in egUsers" :key="user.id" :value="user.id">
                  {{ user.realname }} ({{ user.student_id }})
                </option>
              </select>
              <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-slate-500">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <p class="text-[11px] text-slate-500">Only students assigned to the experimental group (EG) are selectable for cognitive building.</p>
          </div>

          <!-- Build Mode Radio Group -->
          <div class="space-y-3">
            <span class="block text-xs font-semibold text-slate-400 uppercase tracking-widest">Build Pipeline Mode</span>
            
            <div class="space-y-3">
              <!-- Resume -->
              <label class="flex items-start p-3 bg-slate-950/40 border border-slate-850 hover:bg-slate-950/60 rounded-xl cursor-pointer transition-all duration-200">
                <input
                  v-model="buildMode"
                  type="radio"
                  value="resume"
                  :disabled="modelStore.buildStatus === 'running'"
                  class="mt-1 focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-slate-800 bg-slate-900"
                />
                <span class="ml-3 flex flex-col">
                  <span class="text-xs font-bold text-slate-300">Resume / Incremental Build</span>
                  <span class="text-[10px] text-slate-500 mt-0.5">Build only missing layers, preserving completed steps.</span>
                </span>
              </label>

              <!-- Rebuild L2+ -->
              <label class="flex items-start p-3 bg-slate-950/40 border border-slate-850 hover:bg-slate-950/60 rounded-xl cursor-pointer transition-all duration-200">
                <input
                  v-model="buildMode"
                  type="radio"
                  value="rebuild_l2_up"
                  :disabled="modelStore.buildStatus === 'running'"
                  class="mt-1 focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-slate-800 bg-slate-900"
                />
                <span class="ml-3 flex flex-col">
                  <span class="text-xs font-bold text-slate-300">Regenerate L2+ (Insight Layer)</span>
                  <span class="text-[10px] text-slate-500 mt-0.5">Keeps L0 and L1 clusters, rebuilds high-level insights.</span>
                </span>
              </label>

              <!-- Rebuild L1+ -->
              <label class="flex items-start p-3 bg-slate-950/40 border border-slate-850 hover:bg-slate-950/60 rounded-xl cursor-pointer transition-all duration-200">
                <input
                  v-model="buildMode"
                  type="radio"
                  value="rebuild_l1_up"
                  :disabled="modelStore.buildStatus === 'running'"
                  class="mt-1 focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-slate-800 bg-slate-900"
                />
                <span class="ml-3 flex flex-col">
                  <span class="text-xs font-bold text-slate-300">Rebuild L1+ from L0</span>
                  <span class="text-[10px] text-slate-500 mt-0.5">Rebuilds clustering and dimensions from extracted keyinfo.</span>
                </span>
              </label>

              <!-- Full Rebuild -->
              <label class="flex items-start p-3 bg-slate-950/40 border border-slate-850 hover:bg-slate-950/60 rounded-xl cursor-pointer transition-all duration-200">
                <input
                  v-model="buildMode"
                  type="radio"
                  value="rebuild_full"
                  :disabled="modelStore.buildStatus === 'running'"
                  class="mt-1 focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-slate-850 bg-slate-900"
                />
                <span class="ml-3 flex flex-col">
                  <span class="text-xs font-bold text-slate-300">Full Rebuild (Scrape and Re-extract)</span>
                  <span class="text-[10px] text-slate-500 mt-0.5">Deletes all model files and restarts extraction from raw journals.</span>
                </span>
              </label>
            </div>
          </div>

          <!-- Trigger Button -->
          <div class="pt-4">
            <button
              @click="startBuild"
              :disabled="!selectedUserId || modelStore.buildStatus === 'running'"
              class="w-full inline-flex items-center justify-center px-6 py-3.5 border border-transparent text-sm font-semibold rounded-xl shadow-lg text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 transform active:scale-[0.98]"
            >
              <!-- Spinning Icon -->
              <svg v-if="modelStore.buildStatus === 'running'" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <!-- Sparkles Icon -->
              <svg v-else class="-ml-1 mr-2 h-5 w-5 text-indigo-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span v-if="modelStore.buildStatus === 'running'">Build Executing...</span>
              <span v-else-if="buildMode === 'rebuild_full'">Run Full Rebuild</span>
              <span v-else-if="buildMode === 'rebuild_l1_up'">Rebuild L1-L4</span>
              <span v-else-if="buildMode === 'rebuild_l2_up'">Regenerate Insights L2+</span>
              <span v-else>Trigger / Resume Model</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Right Column: Model Config Editor & Live Logging -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Configuration Editor Card -->
        <div class="bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl p-6 rounded-2xl shadow-xl space-y-4">
          <div class="flex items-center justify-between pb-2 border-b border-slate-850">
            <div class="flex items-center space-x-2">
              <svg class="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 class="font-bold text-slate-200">Model Tuning Parameters</h3>
            </div>
            <span v-if="selectedUserId && !modelStore.isLoadingConfig" class="text-xs text-slate-500 font-mono">`model_config.json`</span>
          </div>

          <div v-if="modelStore.isLoadingConfig" class="flex flex-col items-center justify-center py-10 space-y-3">
            <div class="h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-xs text-slate-500">Querying user configuration parameters...</p>
          </div>
          
          <div v-else-if="modelStore.configError" class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center space-x-2">
            <svg class="h-5 w-5 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span><strong>Load Error:</strong> {{ modelStore.configError }}</span>
          </div>

          <textarea
            v-model="modelConfigContent"
            :disabled="!selectedUserId || modelStore.buildStatus === 'running' || modelStore.isLoadingConfig"
            class="w-full h-64 p-4 font-mono text-xs bg-slate-950 border border-slate-850 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none custom-scrollbar text-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed resize-none transition-all duration-250"
            placeholder="Select a student to edit clustering limits, UMAP dimensions, HDBSCAN size, or weights..."
          ></textarea>
          
          <div class="flex items-center justify-between pt-2">
            <button
              @click="saveConfig"
              :disabled="!selectedUserId || modelStore.buildStatus === 'running' || modelStore.isLoadingConfig || modelStore.isSavingConfig"
              class="inline-flex items-center px-4 py-2 border border-slate-800 text-xs font-semibold rounded-xl text-slate-300 bg-slate-950 hover:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
            >
              <svg v-if="modelStore.isSavingConfig" class="animate-spin -ml-1 mr-2 h-4 w-4 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                 <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span v-if="modelStore.isSavingConfig">Saving Config...</span>
              <span v-else>Save Configuration</span>
            </button>
            <transition name="fade">
              <span v-if="modelStore.saveSuccess" class="text-xs text-emerald-400 font-semibold flex items-center space-x-1.5">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
                <span>Config successfully saved</span>
              </span>
            </transition>
          </div>
        </div>

        <!-- Live Log Output Card -->
        <div v-if="modelStore.buildProcessLog" class="bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl rounded-2xl shadow-xl overflow-hidden flex flex-col">
          <div class="flex justify-between items-center p-4 border-b border-slate-850 bg-slate-950/40">
            <h3 class="font-semibold text-sm text-slate-300 flex items-center space-x-2">
              <span class="relative flex h-2 w-2">
                <span :class="modelStore.isStreaming ? 'animate-ping' : ''" class="absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span :class="modelStore.isStreaming ? 'bg-indigo-500' : 'bg-slate-600'" class="relative inline-flex rounded-full h-2 w-2"></span>
              </span>
              <span>Pipeline Stream Output</span>
            </h3>
            <span v-if="modelStore.isStreaming" class="text-[10px] text-indigo-400 font-bold uppercase tracking-wider font-mono animate-pulse">Streaming Live</span>
            <span v-else-if="modelStore.buildStatus === 'running'" class="text-[10px] text-yellow-400 font-bold uppercase tracking-wider font-mono">Connecting...</span>
            <span v-else class="text-[10px] text-slate-500 font-bold uppercase tracking-wider font-mono">Stream Terminated</span>
          </div>
          <pre ref="logContainer" class="whitespace-pre-wrap overflow-y-auto custom-scrollbar h-80 p-5 bg-slate-950 text-slate-300 font-mono text-[11px] leading-relaxed select-text">{{ modelStore.buildProcessLog }}</pre>
        </div>

        <!-- Pipeline Notifications -->
        <div v-if="modelStore.error" class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center space-x-2 animate-pulse">
          <svg class="h-5 w-5 text-red-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span><strong>Build Failure:</strong> {{ modelStore.error }}</span>
        </div>
        
        <div v-if="modelStore.buildStatus === 'completed'" class="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <svg class="h-5 w-5 text-emerald-450 shrink-0 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span><strong>Pipeline Succeeded:</strong> Knowledge model constructed. The cognitive graph is ready for inspection.</span>
          </div>
          <router-link to="/inspect" class="text-xs text-indigo-400 hover:text-indigo-300 font-bold flex items-center space-x-1">
            <span>View Graph</span>
            <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted, watchEffect, computed } from 'vue';
import { useModelStore } from '@/stores/modelStore';

const modelStore = useModelStore();
const selectedUserId = ref(null);
const buildMode = ref('resume'); // 'resume', 'rebuild_l1_up', 'rebuild_full', 'rebuild_l2_up'
const logContainer = ref(null);
const modelConfigContent = ref('');

onMounted(() => {
  modelStore.fetchUsers();
});

const egUsers = computed(() => {
  if (modelStore.users) {
    return modelStore.users.filter(user => user.group === 'EG');
  }
  return [];
});

onUnmounted(() => {
    modelStore.closeStream();
});

const startBuild = () => {
  if (selectedUserId.value) {
    modelStore.startBuildForUser(selectedUserId.value, buildMode.value);
  }
};

const saveConfig = () => {
    if (selectedUserId.value) {
        modelStore.saveModelConfig(selectedUserId.value, modelConfigContent.value);
    }
};

watch(selectedUserId, (newUserId) => {
    if (newUserId) {
        modelStore.checkBuildStatus(newUserId);
        modelStore.fetchModelConfig(newUserId);
    } else {
        modelStore.buildStatus = 'not_started';
        modelStore.buildProcessLog = '';
        modelConfigContent.value = '';
    }
    buildMode.value = 'resume';
});

watchEffect(() => {
    modelConfigContent.value = modelStore.currentConfig;
});

watch(() => modelStore.buildProcessLog, async () => {
  await nextTick();
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight;
  }
});
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #020617; } 
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 99px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>