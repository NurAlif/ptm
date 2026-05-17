<template>
  <div class="flex h-screen bg-slate-900 text-slate-100 font-sans">
    <!-- Sidebar -->
    <aside class="w-64 bg-gradient-to-b from-slate-950 to-slate-900 border-r border-slate-800 flex flex-col shadow-2xl z-10">
      <!-- Sidebar Header -->
      <div class="p-6 border-b border-slate-800/80 bg-slate-950/40 flex items-center space-x-3">
        <div class="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <div>
          <h1 class="text-md font-bold tracking-wider bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">LINGOJOURN</h1>
          <p class="text-xs text-slate-500 font-medium">Teacher Portal</p>
        </div>
      </div>

      <!-- Navigation Menu -->
      <nav class="flex-grow px-4 py-6 space-y-1.5 overflow-y-auto custom-scrollbar">
        <!-- Dashboard Link -->
        <router-link to="/" class="nav-item group" active-class="active-item">
          <svg class="h-5 w-5 icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" />
          </svg>
          <span class="font-medium tracking-wide">Dashboard</span>
          <span class="active-indicator"></span>
        </router-link>

        <!-- Build Model Link -->
        <router-link to="/build" class="nav-item group" active-class="active-item">
          <svg class="h-5 w-5 icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <span class="font-medium tracking-wide">Build Model</span>
          <span class="active-indicator"></span>
        </router-link>

        <!-- Inspect Model Link -->
        <router-link to="/inspect" class="nav-item group" active-class="active-item">
          <svg class="h-5 w-5 icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span class="font-medium tracking-wide">Inspect Model</span>
          <span class="active-indicator"></span>
        </router-link>


      </nav>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-grow bg-slate-950 overflow-auto flex flex-col">
      <!-- Global Top Bar (adds depth and consistency) -->
      <header class="h-16 border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md flex items-center justify-between px-8 z-0">
        <div class="text-xs text-slate-500 font-medium font-mono uppercase tracking-wider">
          SYSTEM STATUS: ONLINE
        </div>
        <div class="flex items-center space-x-2">
          <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-xs text-slate-400 font-medium">Automatic RAG Pipeline Active</span>
        </div>
      </header>

      <!-- Main Panel Scrollable Content -->
      <div class="flex-grow p-8">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
// Authentication fully bypassed - profile details and signout buttons removed
</script>

<style scoped>
.nav-item {
  @apply flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium border border-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/40 hover:border-slate-800/60 transition-all duration-200 cursor-pointer relative;
}

.active-item {
  @apply text-indigo-400 bg-indigo-500/10 border-indigo-500/20 hover:text-indigo-400 hover:bg-indigo-500/10 hover:border-indigo-500/20;
}

.active-item .icon {
  @apply text-indigo-400 filter drop-shadow-[0_0_8px_rgba(99,102,241,0.5)];
}

.active-indicator {
  @apply absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-l-full scale-0 transition-transform duration-200;
}

.active-item .active-indicator {
  @apply scale-100;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 99px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>
