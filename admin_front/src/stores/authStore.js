import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: { id: 1, username: 'admin', realname: 'Administrator', is_admin: true },
    token: 'mock_jwt_token_for_instant_bypass',
    error: null,
    isLoading: false,
  }),
  getters: {
    isAuthenticated: () => true,
  },
  actions: {
    async login() {
      return true;
    },
    async fetchUser() {
      return;
    },
    logout() {
      // Bypassed, do nothing
    },
  },
});

