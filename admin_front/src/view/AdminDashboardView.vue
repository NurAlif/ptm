<template>
  <div class="space-y-8 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-800">
      <div>
        <h2 class="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">Admin Dashboard</h2>
        <p class="text-slate-400 mt-2 text-sm max-w-2xl">
          Welcome to LingoJourn Teacher Portal. Monitor cognitive building and automatic RAG evaluations.
        </p>
      </div>
      <div class="mt-4 md:mt-0 flex items-center space-x-2">
        <span class="h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
        <span class="text-xs text-indigo-400 font-semibold uppercase tracking-wider font-mono">System Online</span>
      </div>
    </div>

    <!-- Quick Action Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Card 1: Build Model -->
      <router-link to="/build" class="group bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800/80 hover:border-indigo-500/50 backdrop-blur-xl p-6 rounded-2xl shadow-xl hover:shadow-[0_0_25px_rgba(99,102,241,0.15)] transition-all duration-300 flex flex-col justify-between h-64">
        <div>
          <div class="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 group-hover:bg-indigo-500/20 transition-all duration-300">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h3 class="mt-4 text-lg font-bold text-slate-200 group-hover:text-indigo-400 transition-colors duration-200">Build Model</h3>
          <p class="mt-2 text-slate-400 text-xs leading-relaxed">
            Trigger and monitor the background construction of cognitive hierarchical knowledge models from student journal entries.
          </p>
        </div>
        <div class="flex items-center text-xs font-bold text-indigo-400 mt-4 group-hover:translate-x-1 transition-transform duration-200">
          Configure & Build →
        </div>
      </router-link>

      <!-- Card 2: Inspect Model -->
      <router-link to="/inspect" class="group bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800/80 hover:border-indigo-500/50 backdrop-blur-xl p-6 rounded-2xl shadow-xl hover:shadow-[0_0_25px_rgba(99,102,241,0.15)] transition-all duration-300 flex flex-col justify-between h-64">
        <div>
          <div class="h-12 w-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 group-hover:bg-indigo-500/20 transition-all duration-300">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          </div>
          <h3 class="mt-4 text-lg font-bold text-slate-200 group-hover:text-indigo-400 transition-colors duration-200">Inspect Model</h3>
          <p class="mt-2 text-slate-400 text-xs leading-relaxed">
            View and interact with generated knowledge graph models using our real-time interactive explorer.
          </p>
        </div>
        <div class="flex items-center text-xs font-bold text-indigo-400 mt-4 group-hover:translate-x-1 transition-transform duration-200">
          Open Graph Explorer →
        </div>
      </router-link>



    </div>
  </div>
</template>

<script setup>
// No extra scripts needed for static dashboard routing
</script>
