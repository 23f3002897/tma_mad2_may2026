<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
      <div>
        <h2 class="fw-bold mb-1">Manage Trek Staff & Guides</h2>
        <p class="text-muted mb-0">Create and oversee professional staff accounts responsible for guiding trek routes.</p>
      </div>
      <button @click="openCreateModal" class="btn btn-warning text-dark fw-bold shadow-sm d-flex align-items-center">
        <span class="fs-5 me-1">+</span> Create Staff Account
      </button>
    </div>

    <Alert :message="error" type="danger" @close="error = ''" />
    <Alert :message="success" type="success" @close="success = ''" />

    <!-- Staff Table -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-dark">
            <tr>
              <th class="py-3 px-4">Staff Member</th>
              <th class="py-3">Contact Phone</th>
              <th class="py-3">Specialization / Expertise</th>
              <th class="py-3">Account Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="staff in staffList" :key="staff.id">
              <td class="px-4">
                <div class="fw-bold text-dark">{{ staff.full_name }}</div>
                <div class="text-muted fs-7">{{ staff.email }}</div>
              </td>
              <td>{{ staff.phone || 'N/A' }}</td>
              <td>
                <span class="badge bg-info text-dark fw-semibold px-3 py-1">
                  {{ staff.specialization || 'General Trek Leader' }}
                </span>
              </td>
              <td>
                <span class="badge rounded-pill" :class="staff.is_active ? 'bg-success' : 'bg-danger'">
                  {{ staff.is_active ? 'Active' : 'Deactivated / Blacklisted' }}
                </span>
              </td>
            </tr>
            <tr v-if="staffList.length === 0">
              <td colspan="4" class="text-center py-5 text-muted">No staff accounts found. Create your first Trek Guide above!</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Staff Modal -->
    <div class="modal fade" id="staffModal" tabindex="-1" aria-labelledby="staffModalLabel" aria-hidden="true" ref="modalEl">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
          <div class="modal-header bg-dark-premium text-white py-3">
            <h5 class="modal-title fw-bold" id="staffModalLabel">Create Trek Staff Account</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <form @submit.prevent="saveStaff">
            <div class="modal-body p-4">
              <div class="mb-3">
                <label class="form-label fw-semibold">Full Name *</label>
                <input type="text" v-model="form.full_name" class="form-control" placeholder="e.g. Ravi Kumar" required />
              </div>
              <div class="mb-3">
                <label class="form-label fw-semibold">Email Address *</label>
                <input type="email" v-model="form.email" class="form-control" placeholder="e.g. ravi.staff@tma.com" required />
              </div>
              <div class="mb-3">
                <label class="form-label fw-semibold">Password * (min 6 chars)</label>
                <input type="password" v-model="form.password" class="form-control" placeholder="Create staff password..." minlength="6" required />
              </div>
              <div class="mb-3">
                <label class="form-label fw-semibold">Contact Phone</label>
                <input type="text" v-model="form.phone" class="form-control" placeholder="e.g. 9876543210" />
              </div>
              <div class="mb-3">
                <label class="form-label fw-semibold">Specialization / Expertise</label>
                <input type="text" v-model="form.specialization" class="form-control" placeholder="e.g. High Altitude Rescue Specialist" />
              </div>
            </div>

            <div class="modal-footer bg-light px-4 py-3">
              <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-warning text-dark rounded-pill px-4 fw-bold" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span>Create Staff</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api';
import Alert from '../components/Alert.vue';
import * as bootstrap from 'bootstrap';

export default {
  name: 'ManageStaff',
  components: { Alert },
  data() {
    return {
      staffList: [],
      loading: false,
      error: '',
      success: '',
      modalInstance: null,
      form: {
        full_name: '',
        email: '',
        password: '',
        phone: '',
        specialization: 'High Altitude Guide'
      }
    };
  },
  methods: {
    async fetchStaff() {
      try {
        const res = await api.getAdminStaff();
        this.staffList = res.staff || [];
      } catch (err) {
        this.error = err.message || 'Failed to fetch staff list.';
      }
    },
    openCreateModal() {
      this.form = {
        full_name: '',
        email: '',
        password: '',
        phone: '',
        specialization: 'High Altitude Guide'
      };
      if (!this.modalInstance && this.$refs.modalEl) {
        this.modalInstance = new bootstrap.Modal(this.$refs.modalEl);
      }
      this.modalInstance?.show();
    },
    async saveStaff() {
      this.loading = true;
      this.error = '';
      this.success = '';
      try {
        const res = await api.createStaff(this.form);
        this.success = res.message || 'Staff account created successfully!';
        this.modalInstance?.hide();
        await this.fetchStaff();
      } catch (err) {
        this.error = err.message || 'Failed to create staff account.';
      } finally {
        this.loading = false;
      }
    }
  },
  mounted() {
    this.fetchStaff();
  }
};
</script>

<style scoped>
.bg-dark-premium {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}
.fs-7 {
  font-size: 0.825rem;
}
</style>
