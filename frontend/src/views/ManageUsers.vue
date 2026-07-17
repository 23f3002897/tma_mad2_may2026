<template>
  <div class="container py-4">
    <div class="mb-4 border-bottom pb-3">
      <h2 class="fw-bold mb-1">Manage Users & Blacklist Control</h2>
      <p class="text-muted mb-0">View all registered trekkers and staff. Toggle account status (`is_active`) to blacklist unauthorized or fraudulent users.</p>
    </div>

    <Alert :message="error" type="danger" @close="error = ''" />
    <Alert :message="success" type="success" @close="success = ''" />

    <!-- Users Table -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-dark">
            <tr>
              <th class="py-3 px-4">User Details</th>
              <th class="py-3">Role</th>
              <th class="py-3">Registration Date</th>
              <th class="py-3">Status</th>
              <th class="py-3 text-end px-4">Blacklist / Activate Control</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="px-4">
                <div class="fw-bold text-dark">{{ user.full_name }}</div>
                <div class="text-muted fs-7">{{ user.email }}</div>
              </td>
              <td>
                <span class="badge px-3 py-1" :class="user.role === 'staff' ? 'bg-warning text-dark' : 'bg-info text-dark'">
                  {{ user.role.toUpperCase() }}
                </span>
              </td>
              <td class="fs-7 text-muted">{{ user.created_at || 'N/A' }}</td>
              <td>
                <span class="badge rounded-pill px-3 py-1" :class="user.is_active ? 'bg-success' : 'bg-danger'">
                  {{ user.is_active ? 'Active' : 'Blacklisted' }}
                </span>
              </td>
              <td class="text-end px-4">
                <button 
                  @click="toggleActive(user)" 
                  class="btn btn-sm rounded-pill px-4 fw-semibold"
                  :class="user.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                  :disabled="loadingId === user.id"
                >
                  <span v-if="loadingId === user.id" class="spinner-border spinner-border-sm me-1"></span>
                  <span>{{ user.is_active ? 'Blacklist User' : 'Reactivate User' }}</span>
                </button>
              </td>
            </tr>
            <tr v-if="users.length === 0">
              <td colspan="5" class="text-center py-5 text-muted">No users registered yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api';
import Alert from '../components/Alert.vue';

export default {
  name: 'ManageUsers',
  components: { Alert },
  data() {
    return {
      users: [],
      error: '',
      success: '',
      loadingId: null
    };
  },
  methods: {
    async fetchUsers() {
      try {
        const res = await api.getAdminUsers();
        this.users = res.users || [];
      } catch (err) {
        this.error = err.message || 'Failed to load user accounts.';
      }
    },
    async toggleActive(user) {
      const actionStr = user.is_active ? 'blacklist' : 'reactivate';
      if (!confirm(`Are you sure you want to ${actionStr} user "${user.email}"?`)) return;

      this.loadingId = user.id;
      this.error = '';
      this.success = '';
      try {
        const res = await api.toggleUserActive(user.id);
        this.success = res.message || `User status updated successfully.`;
        await this.fetchUsers();
      } catch (err) {
        this.error = err.message || 'Failed to toggle user status.';
      } finally {
        this.loadingId = null;
      }
    }
  },
  mounted() {
    this.fetchUsers();
  }
};
</script>

<style scoped>
.fs-7 {
  font-size: 0.825rem;
}
</style>
