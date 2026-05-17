import { createRouter, createWebHistory } from 'vue-router';

import AdminLayout from '@/view/AdminLayout.vue';
import AdminDashboardView from '@/view/AdminDashboardView.vue';
import BuildModelView from '@/view/BuildModelView.vue';
import InspectModelView from '@/view/InspectModelView.vue';

const routes = [
  {
    path: '/',
    component: AdminLayout,
    children: [
      { path: '', name: 'AdminDashboard', component: AdminDashboardView },
      { path: 'build', name: 'BuildModel', component: BuildModelView },
      { path: 'inspect', name: 'InspectModel', component: InspectModelView },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
