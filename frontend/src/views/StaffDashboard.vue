<template>
  <div class="container py-4">
    <div class="mb-4 border-bottom pb-3">
      <h2 class="fw-bold mb-1">Trek Staff & Guide Dashboard</h2>
      <p class="text-muted mb-0">Manage your assigned trekking routes, update trail statuses, adjust live capacity, and view registered participants.</p>
    </div>

    <Alert :message="error" type="danger" @close="error = ''" />
    <Alert :message="success" type="success" @close="success = ''" />

    <div class="row g-4">
      <div v-for="trek in treks" :key="trek.id" class="col-md-6 col-lg-4">
        <div class="card border-0 shadow-sm rounded-4 h-100 d-flex flex-column justify-content-between overflow-hidden">
          <div class="card-header bg-dark-premium text-white py-3 d-flex justify-content-between align-items-center">
            <span class="badge bg-warning text-dark fw-bold">{{ trek.difficulty }}</span>
            <span class="fs-7 opacity-75">{{ trek.start_date }}</span>
          </div>

          <div class="card-body p-4">
            <h5 class="fw-bold text-primary mb-1">{{ trek.name }}</h5>
            <p class="text-muted fs-7 mb-3">{{ trek.location }}</p>
            <p class="fs-7 text-secondary mb-3">{{ trek.description }}</p>

            <hr class="my-3 opacity-10">

            <div class="d-flex justify-content-between align-items-center mb-3">
              <span class="fs-7 fw-semibold">Current Status:</span>
              <span class="badge rounded-pill px-3 py-1" :class="statusBadge(trek.status)">{{ trek.status }}</span>
            </div>

            <div class="d-flex justify-content-between align-items-center mb-3">
              <span class="fs-7 fw-semibold">Capacity (Avail/Total):</span>
              <span class="fw-bold" :class="trek.available_slots === 0 ? 'text-danger' : 'text-success'">
                {{ trek.available_slots }} / {{ trek.total_slots }} Slots
              </span>
            </div>
          </div>

          <div class="card-footer bg-light p-3 border-top d-flex gap-2 justify-content-between">
            <button @click="openManageModal(trek)" class="btn btn-outline-primary btn-sm rounded-pill flex-fill fw-semibold">
              Update Status & Slots
            </button>
            <button @click="openParticipantsModal(trek)" class="btn btn-primary btn-sm rounded-pill flex-fill fw-semibold">
              Participants
            </button>
          </div>
        </div>
      </div>

      <div v-if="treks.length === 0" class="col-12 text-center py-5">
        <div class="card border-0 shadow-sm rounded-4 p-5 bg-light">
          <h4 class="text-muted mb-2">No Treks Assigned Yet</h4>
          <p class="text-secondary fs-7 mb-0">You do not have any active trekking routes assigned to your staff account by the Institute Admin.</p>
        </div>
      </div>
    </div>

    <!-- Manage Status/Slots Modal -->
    <div class="modal fade" id="manageModal" tabindex="-1" aria-labelledby="manageModalLabel" aria-hidden="true" ref="manageModalEl">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
          <div class="modal-header bg-dark-premium text-white py-3">
            <h5 class="modal-title fw-bold" id="manageModalLabel">Manage Route: {{ selectedTrek?.name }}</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <form @submit.prevent="updateTrekDetails">
            <div class="modal-body p-4">
              <div class="mb-3">
                <label class="form-label fw-semibold">Trek Status *</label>
                <select v-model="editForm.status" class="form-select" required>
                  <option value="Open">Open (Accepting Bookings)</option>
                  <option value="Closed">Closed (Trail Closed / Full)</option>
                  <option value="Completed">Completed (Trek Finished)</option>
                </select>
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">Available Slots left *</label>
                <input 
                  type="number" 
                  v-model="editForm.available_slots" 
                  class="form-control" 
                  min="0" 
                  :max="selectedTrek?.total_slots" 
                  required 
                />
                <div class="form-text fs-7">Maximum total slots for this trek: {{ selectedTrek?.total_slots }}</div>
              </div>
            </div>

            <div class="modal-footer bg-light px-4 py-3">
              <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary rounded-pill px-4 fw-bold" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span>Save Changes</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Participants Modal -->
    <div class="modal fade" id="participantsModal" tabindex="-1" aria-labelledby="participantsModalLabel" aria-hidden="true" ref="participantsModalEl">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
          <div class="modal-header bg-primary text-white py-3">
            <h5 class="modal-title fw-bold" id="participantsModalLabel">Registered Trekkers: {{ participantsData?.trek_name }}</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <div class="modal-body p-4">
            <div v-if="participantsLoading" class="text-center py-5">
              <span class="spinner-border text-primary"></span>
            </div>
            <div v-else-if="participantsData">
              <div class="d-flex justify-content-between mb-3 bg-light p-3 rounded-3 border">
                <div><span class="fw-semibold">Total Capacity:</span> {{ participantsData.total_slots }}</div>
                <div><span class="fw-semibold text-success">Available Slots:</span> {{ participantsData.available_slots }}</div>
                <div><span class="fw-semibold text-primary">Total Bookings:</span> {{ participantsData.participants.length }}</div>
              </div>

              <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>Trekker Name</th>
                      <th>Email Address</th>
                      <th>Tickets Booked</th>
                      <th>Booking Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in participantsData.participants" :key="p.id">
                      <td class="fw-bold">{{ p.user_name }}</td>
                      <td class="text-muted fs-7">{{ p.user_email }}</td>
                      <td><span class="badge bg-primary rounded-pill">{{ p.tickets_booked }}</span></td>
                      <td class="fs-7 text-muted">{{ p.booking_date }}</td>
                      <td>
                        <span class="badge rounded-pill" :class="p.status === 'Booked' ? 'bg-success' : 'bg-secondary'">
                          {{ p.status }}
                        </span>
                      </td>
                    </tr>
                    <tr v-if="participantsData.participants.length === 0">
                      <td colspan="5" class="text-center py-4 text-muted">No trekkers have booked this route yet.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="modal-footer bg-light px-4 py-3">
            <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Close</button>
          </div>
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
  name: 'StaffDashboard',
  components: { Alert },
  data() {
    return {
      treks: [],
      loading: false,
      error: '',
      success: '',
      selectedTrek: null,
      editForm: {
        status: 'Open',
        available_slots: 0
      },
      manageModalInstance: null,
      participantsModalInstance: null,
      participantsData: null,
      participantsLoading: false
    };
  },
  methods: {
    statusBadge(status) {
      if (status === 'Open') return 'bg-success';
      if (status === 'Closed') return 'bg-secondary';
      return 'bg-info text-dark';
    },
    async fetchStaffTreks() {
      try {
        const res = await api.getStaffTreks();
        this.treks = res.treks || [];
      } catch (err) {
        this.error = err.message || 'Failed to fetch assigned treks.';
      }
    },
    openManageModal(trek) {
      this.selectedTrek = trek;
      this.editForm = {
        status: trek.status,
        available_slots: trek.available_slots
      };
      if (!this.manageModalInstance && this.$refs.manageModalEl) {
        this.manageModalInstance = new bootstrap.Modal(this.$refs.manageModalEl);
      }
      this.manageModalInstance?.show();
    },
    async updateTrekDetails() {
      if (!this.selectedTrek) return;
      this.loading = true;
      this.error = '';
      this.success = '';
      try {
        const res = await api.updateStaffTrek(this.selectedTrek.id, this.editForm);
        this.success = res.message || 'Trek updated successfully.';
        this.manageModalInstance?.hide();
        await this.fetchStaffTreks();
      } catch (err) {
        this.error = err.message || 'Failed to update trek details.';
      } finally {
        this.loading = false;
      }
    },
    async openParticipantsModal(trek) {
      this.selectedTrek = trek;
      this.participantsData = null;
      this.participantsLoading = true;
      if (!this.participantsModalInstance && this.$refs.participantsModalEl) {
        this.participantsModalInstance = new bootstrap.Modal(this.$refs.participantsModalEl);
      }
      this.participantsModalInstance?.show();

      try {
        const res = await api.getStaffTrekParticipants(trek.id);
        this.participantsData = res;
      } catch (err) {
        this.error = err.message || 'Failed to load participants list.';
      } finally {
        this.participantsLoading = false;
      }
    }
  },
  mounted() {
    this.fetchStaffTreks();
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
