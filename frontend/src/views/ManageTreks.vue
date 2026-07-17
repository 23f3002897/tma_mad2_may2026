<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
      <div>
        <h2 class="fw-bold mb-1">Manage Trekking Routes</h2>
        <p class="text-muted mb-0">Create new treks, update slot allocations, assign staff guides, and manage statuses.</p>
      </div>
      <button @click="openCreateModal" class="btn btn-primary fw-semibold shadow-sm d-flex align-items-center">
        <span class="fs-5 me-1">+</span> Create New Trek
      </button>
    </div>

    <Alert :message="error" type="danger" @close="error = ''" />
    <Alert :message="success" type="success" @close="success = ''" />

    <!-- Treks Table -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-dark">
            <tr>
              <th class="py-3 px-4">Trek Name & Location</th>
              <th class="py-3">Difficulty / Duration</th>
              <th class="py-3">Dates</th>
              <th class="py-3">Slots (Avail/Total)</th>
              <th class="py-3">Assigned Staff</th>
              <th class="py-3">Status</th>
              <th class="py-3 text-end px-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trek in treks" :key="trek.id">
              <td class="px-4">
                <div class="fw-bold text-primary">{{ trek.name }}</div>
                <div class="text-muted fs-7">{{ trek.location }}</div>
              </td>
              <td>
                <span class="badge me-1" :class="difficultyBadge(trek.difficulty)">{{ trek.difficulty }}</span>
                <span class="text-muted fs-7">{{ trek.duration_days }} Days</span>
              </td>
              <td class="fs-7">
                <div>{{ trek.start_date }}</div>
                <div class="text-muted">to {{ trek.end_date }}</div>
              </td>
              <td>
                <span class="fw-bold" :class="trek.available_slots === 0 ? 'text-danger' : 'text-success'">
                  {{ trek.available_slots }}
                </span>
                <span class="text-muted"> / {{ trek.total_slots }}</span>
              </td>
              <td>
                <span v-if="trek.assigned_staff_id" class="badge bg-warning text-dark fw-semibold">
                  {{ trek.assigned_staff_name }}
                </span>
                <span v-else class="badge bg-secondary opacity-75">Unassigned</span>
              </td>
              <td>
                <span class="badge rounded-pill" :class="statusBadge(trek.status)">{{ trek.status }}</span>
              </td>
              <td class="text-end px-4">
                <button @click="openEditModal(trek)" class="btn btn-outline-primary btn-sm rounded-pill me-1 px-3">
                  Edit
                </button>
                <button @click="handleDelete(trek)" class="btn btn-outline-danger btn-sm rounded-pill px-3">
                  Delete
                </button>
              </td>
            </tr>
            <tr v-if="treks.length === 0">
              <td colspan="7" class="text-center py-5 text-muted">No trekking routes available. Click "Create New Trek" above!</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create / Edit Modal -->
    <div class="modal fade" id="trekModal" tabindex="-1" aria-labelledby="trekModalLabel" aria-hidden="true" ref="modalEl">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
          <div class="modal-header bg-dark-premium text-white py-3">
            <h5 class="modal-title fw-bold" id="trekModalLabel">
              {{ isEditing ? 'Edit Trek: ' + form.name : 'Create New Trekking Route' }}
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <form @submit.prevent="saveTrek">
            <div class="modal-body p-4">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label fw-semibold">Trek Name *</label>
                  <input type="text" v-model="form.name" class="form-control" placeholder="e.g. Kedarkantha Summit" required />
                </div>
                <div class="col-md-6">
                  <label class="form-label fw-semibold">Location / State *</label>
                  <input type="text" v-model="form.location" class="form-control" placeholder="e.g. Uttarkashi, Uttarakhand" required />
                </div>
                
                <div class="col-md-4">
                  <label class="form-label fw-semibold">Difficulty Level *</label>
                  <select v-model="form.difficulty" class="form-select" required>
                    <option value="Easy">Easy</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label fw-semibold">Duration (Days) *</label>
                  <input type="number" v-model="form.duration_days" class="form-control" min="1" required />
                </div>
                <div class="col-md-4">
                  <label class="form-label fw-semibold">Total Capacity Slots *</label>
                  <input type="number" v-model="form.total_slots" class="form-control" min="1" required />
                </div>

                <div class="col-md-4">
                  <label class="form-label fw-semibold">Start Date *</label>
                  <input type="date" v-model="form.start_date" class="form-control" required />
                </div>
                <div class="col-md-4">
                  <label class="form-label fw-semibold">End Date *</label>
                  <input type="date" v-model="form.end_date" class="form-control" required />
                </div>
                <div class="col-md-4">
                  <label class="form-label fw-semibold">Booking Status *</label>
                  <select v-model="form.status" class="form-select" required>
                    <option value="Open">Open</option>
                    <option value="Closed">Closed</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>

                <div class="col-12">
                  <label class="form-label fw-semibold">Assign Staff Guide (Optional)</label>
                  <select v-model="form.assigned_staff_id" class="form-select">
                    <option :value="null">-- Unassigned --</option>
                    <option v-for="staff in staffList" :key="staff.id" :value="staff.id">
                      {{ staff.full_name }} ({{ staff.specialization || 'General Guide' }})
                    </option>
                  </select>
                </div>

                <div class="col-12">
                  <label class="form-label fw-semibold">Description / Itinerary Details</label>
                  <textarea v-model="form.description" class="form-control" rows="3" placeholder="Provide trail description and important instructions..."></textarea>
                </div>
              </div>
            </div>

            <div class="modal-footer bg-light px-4 py-3">
              <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary rounded-pill px-4 fw-bold" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span>{{ isEditing ? 'Update Trek' : 'Create Trek' }}</span>
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
  name: 'ManageTreks',
  components: { Alert },
  data() {
    return {
      treks: [],
      staffList: [],
      loading: false,
      error: '',
      success: '',
      isEditing: false,
      editId: null,
      modalInstance: null,
      form: {
        name: '',
        location: '',
        difficulty: 'Easy',
        duration_days: 2,
        total_slots: 20,
        status: 'Open',
        start_date: '',
        end_date: '',
        description: '',
        assigned_staff_id: null
      }
    };
  },
  methods: {
    difficultyBadge(diff) {
      if (diff === 'Easy') return 'bg-success';
      if (diff === 'Moderate') return 'bg-warning text-dark';
      return 'bg-danger';
    },
    statusBadge(status) {
      if (status === 'Open') return 'bg-success';
      if (status === 'Closed') return 'bg-secondary';
      return 'bg-info text-dark';
    },
    async fetchData() {
      try {
        const [treksRes, staffRes] = await Promise.all([
          api.getAdminTreks(),
          api.getAdminStaff()
        ]);
        this.treks = treksRes.treks || [];
        this.staffList = staffRes.staff || [];
      } catch (err) {
        this.error = err.message || 'Failed to fetch treks or staff.';
      }
    },
    openCreateModal() {
      this.isEditing = false;
      this.editId = null;
      this.form = {
        name: '',
        location: '',
        difficulty: 'Easy',
        duration_days: 2,
        total_slots: 20,
        status: 'Open',
        start_date: '',
        end_date: '',
        description: '',
        assigned_staff_id: null
      };
      if (!this.modalInstance && this.$refs.modalEl) {
        this.modalInstance = new bootstrap.Modal(this.$refs.modalEl);
      }
      this.modalInstance?.show();
    },
    openEditModal(trek) {
      this.isEditing = true;
      this.editId = trek.id;
      this.form = {
        name: trek.name,
        location: trek.location,
        difficulty: trek.difficulty,
        duration_days: trek.duration_days,
        total_slots: trek.total_slots,
        status: trek.status,
        start_date: trek.start_date,
        end_date: trek.end_date,
        description: trek.description,
        assigned_staff_id: trek.assigned_staff_id || null
      };
      if (!this.modalInstance && this.$refs.modalEl) {
        this.modalInstance = new bootstrap.Modal(this.$refs.modalEl);
      }
      this.modalInstance?.show();
    },
    async saveTrek() {
      this.loading = true;
      this.error = '';
      this.success = '';
      try {
        if (this.isEditing) {
          const res = await api.updateTrek(this.editId, this.form);
          this.success = res.message || 'Trek updated successfully!';
        } else {
          const res = await api.createTrek(this.form);
          this.success = res.message || 'Trek created successfully!';
        }
        this.modalInstance?.hide();
        await this.fetchData();
      } catch (err) {
        this.error = err.message || 'Failed to save trek details.';
      } finally {
        this.loading = false;
      }
    },
    async handleDelete(trek) {
      if (!confirm(`Are you sure you want to delete trek "${trek.name}"? This action cannot be undone.`)) return;
      try {
        const res = await api.deleteTrek(trek.id);
        this.success = res.message || 'Trek deleted successfully.';
        await this.fetchData();
      } catch (err) {
        this.error = err.message || 'Failed to delete trek.';
      }
    }
  },
  mounted() {
    this.fetchData();
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
