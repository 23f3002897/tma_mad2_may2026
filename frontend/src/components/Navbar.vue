<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark-premium sticky-top shadow-sm py-3">
    <div class="container">
      <router-link class="navbar-brand fw-bold d-flex align-items-center" to="/">
        <span>TMA <small class="fw-light fs-6 opacity-75">Trekking System</small></span>
      </router-link>
      
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <!-- Public / Common Link -->
          <li class="nav-item">
            <router-link class="nav-link" to="/" active-class="active">Explore Treks</router-link>
          </li>

          <!-- Admin Navigation -->
          <template v-if="user && user.role === 'admin'">
            <li class="nav-item">
              <router-link class="nav-link" to="/admin" active-class="active">Dashboard</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/treks" active-class="active">Manage Treks</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/staff" active-class="active">Manage Staff</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/admin/users" active-class="active">Users & Blacklist</router-link>
            </li>
          </template>

          <!-- Staff Navigation -->
          <template v-if="user && user.role === 'staff'">
            <li class="nav-item">
              <router-link class="nav-link" to="/staff" active-class="active">Staff Dashboard</router-link>
            </li>
          </template>

          <!-- Trekker (User) Navigation -->
          <template v-if="user && user.role === 'user'">
            <li class="nav-item">
              <router-link class="nav-link" to="/my-bookings" active-class="active">My Bookings</router-link>
            </li>
          </template>
        </ul>

        <ul class="navbar-nav ms-auto align-items-lg-center">
          <!-- Logged in State -->
          <template v-if="user">
            <li class="nav-item me-3 mb-2 mb-lg-0">
              <span class="badge rounded-pill px-3 py-2 fs-7" :class="roleBadgeClass">
                {{ user.role.toUpperCase() }}: {{ user.full_name }}
              </span>
            </li>
            <li class="nav-item me-2">
              <router-link class="btn btn-outline-light btn-sm rounded-pill px-3" to="/profile">Profile</router-link>
            </li>
            <li class="nav-item">
              <button @click="handleLogout" class="btn btn-danger btn-sm rounded-pill px-3">Logout</button>
            </li>
          </template>

          <!-- Guest State -->
          <template v-else>
            <li class="nav-item me-2 mb-2 mb-lg-0">
              <router-link class="btn btn-outline-light btn-sm rounded-pill px-3" to="/login">Login</router-link>
            </li>
            <li class="nav-item">
              <router-link class="btn btn-primary btn-sm rounded-pill px-3 fw-semibold" to="/register">Register</router-link>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
import { getUser, clearToken } from '../services/api';

export default {
  name: 'Navbar',
  data() {
    return {
      user: null
    };
  },
  computed: {
    roleBadgeClass() {
      if (!this.user) return '';
      if (this.user.role === 'admin') return 'bg-danger text-white';
      if (this.user.role === 'staff') return 'bg-warning text-dark fw-bold';
      return 'bg-info text-dark fw-bold';
    }
  },
  methods: {
    refreshUser() {
      this.user = getUser();
    },
    handleLogout() {
      clearToken();
      this.user = null;
      this.$router.push('/login');
    }
  },
  mounted() {
    this.refreshUser();
    // Listen for custom login/update events
    window.addEventListener('auth-change', this.refreshUser);
  },
  beforeUnmount() {
    window.removeEventListener('auth-change', this.refreshUser);
  }
}
</script>

<style scoped>
.bg-dark-premium {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}
.navbar-brand {
  letter-spacing: -0.5px;
}
.fs-7 {
  font-size: 0.825rem;
}
</style>
