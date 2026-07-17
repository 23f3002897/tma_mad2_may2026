import { createRouter, createWebHistory } from 'vue-router';
import { getToken, getUser } from '../services/api';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/UserDashboard.vue'),
    meta: { title: 'Explore Trekking Routes' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guestOnly: true, title: 'Login - TMA' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guestOnly: true, title: 'Register - TMA' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true, title: 'My Profile' }
  },
  {
    path: '/my-bookings',
    name: 'MyBookings',
    component: () => import('../views/MyBookings.vue'),
    meta: { requiresAuth: true, allowedRoles: ['user', 'admin'], title: 'My Bookings & History' }
  },
  // Admin Routes
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, allowedRoles: ['admin'], title: 'Admin Dashboard' }
  },
  {
    path: '/admin/treks',
    name: 'ManageTreks',
    component: () => import('../views/ManageTreks.vue'),
    meta: { requiresAuth: true, allowedRoles: ['admin'], title: 'Manage Trekking Routes' }
  },
  {
    path: '/admin/staff',
    name: 'ManageStaff',
    component: () => import('../views/ManageStaff.vue'),
    meta: { requiresAuth: true, allowedRoles: ['admin'], title: 'Manage Trek Staff' }
  },
  {
    path: '/admin/users',
    name: 'ManageUsers',
    component: () => import('../views/ManageUsers.vue'),
    meta: { requiresAuth: true, allowedRoles: ['admin'], title: 'Manage Users & Blacklist' }
  },
  // Staff Routes
  {
    path: '/staff',
    name: 'StaffDashboard',
    component: () => import('../views/StaffDashboard.vue'),
    meta: { requiresAuth: true, allowedRoles: ['staff', 'admin'], title: 'Staff Dashboard' }
  },
  // Catch-all redirect to Home
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Role-Based Navigation Guard
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Trekking Management Application';
  
  const token = getToken();
  const user = getUser();

  if (to.meta.requiresAuth && !token) {
    return next({ name: 'Login', query: { redirect: to.fullPath } });
  }

  if (to.meta.guestOnly && token && user) {
    if (user.role === 'admin') return next({ name: 'AdminDashboard' });
    if (user.role === 'staff') return next({ name: 'StaffDashboard' });
    return next({ name: 'Home' });
  }

  if (to.meta.allowedRoles && user) {
    if (!to.meta.allowedRoles.includes(user.role)) {
      // Unauthorized role -> redirect to appropriate dashboard
      if (user.role === 'admin') return next({ name: 'AdminDashboard' });
      if (user.role === 'staff') return next({ name: 'StaffDashboard' });
      return next({ name: 'Home' });
    }
  }

  next();
});

export default router;
