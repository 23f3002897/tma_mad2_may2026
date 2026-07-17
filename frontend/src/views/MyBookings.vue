<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3 flex-wrap gap-3">
      <div>
        <h2 class="fw-bold mb-1">My Trek Bookings & History</h2>
        <p class="text-muted mb-0">Track your upcoming summits, review past adventures, or export your complete records.</p>
      </div>
      
      <!-- Asynchronous CSV Export Section (Celery Trigger) -->
      <div class="d-flex align-items-center gap-2">
        <button 
          @click="startCsvExport" 
          class="btn btn-outline-success fw-semibold shadow-sm d-flex align-items-center"
          :disabled="exportLoading"
        >
          <span v-if="exportLoading" class="spinner-border spinner-border-sm me-2"></span>
          <span>{{ exportLoading ? 'Exporting CSV...' : 'Export Bookings CSV' }}</span>
        </button>

        <a 
          v-if="downloadUrl" 
          :href="`http://127.0.0.1:5000${downloadUrl}`" 
          class="btn btn-success fw-bold shadow-sm animate-pulse"
          download
        >
          Download CSV File
        </a>
      </div>
    </div>

    <Alert :message="error" type="danger" @close="error = ''" />
    <Alert :message="success" type="success" @close="success = ''" />
    <Alert :message="exportStatusMessage" type="info" :dismissible="false" v-if="exportStatusMessage" />

    <!-- Bookings Table -->
    <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-dark">
            <tr>
              <th class="py-3 px-4">Trek Route</th>
              <th class="py-3">Location & Difficulty</th>
              <th class="py-3">Tickets Booked</th>
              <th class="py-3">Booking Date</th>
              <th class="py-3">Status</th>
              <th class="py-3 text-end px-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="booking in bookings" :key="booking.id">
              <td class="px-4">
                <div class="fw-bold text-primary fs-6">{{ booking.trek_name }}</div>
                <div class="text-muted fs-7">Booking ID: #{{ booking.id }}</div>
              </td>
              <td>
                <div>{{ booking.location }}</div>
                <span class="badge mt-1" :class="difficultyBadge(booking.difficulty)">{{ booking.difficulty }}</span>
              </td>
              <td>
                <span class="badge bg-primary rounded-pill px-3 py-1 fs-6">{{ booking.tickets_booked }} Ticket(s)</span>
              </td>
              <td class="fs-7 text-muted">{{ booking.booking_date }}</td>
              <td>
                <span class="badge rounded-pill px-3 py-1" :class="statusBadge(booking.status)">
                  {{ booking.status }}
                </span>
              </td>
              <td class="text-end px-4">
                <button 
                  v-if="booking.status === 'Booked'"
                  @click="handleCancel(booking)" 
                  class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-semibold"
                  :disabled="cancellingId === booking.id"
                >
                  <span v-if="cancellingId === booking.id" class="spinner-border spinner-border-sm me-1"></span>
                  <span>Cancel Booking</span>
                </button>
                <span v-else class="text-muted fs-7 opacity-75">No actions</span>
              </td>
            </tr>
            <tr v-if="bookings.length === 0">
              <td colspan="6" class="text-center py-5 text-muted">
                You haven't booked any treks yet. 
                <router-link to="/" class="text-decoration-none fw-bold ms-1">Explore available routes!</router-link>
              </td>
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
  name: 'MyBookings',
  components: { Alert },
  data() {
    return {
      bookings: [],
      error: '',
      success: '',
      cancellingId: null,
      exportLoading: false,
      exportStatusMessage: '',
      downloadUrl: null,
      pollInterval: null
    };
  },
  methods: {
    difficultyBadge(diff) {
      if (diff === 'Easy') return 'bg-success';
      if (diff === 'Moderate') return 'bg-warning text-dark';
      return 'bg-danger';
    },
    statusBadge(status) {
      if (status === 'Booked') return 'bg-success';
      if (status === 'Cancelled') return 'bg-secondary';
      return 'bg-info text-dark';
    },
    async fetchBookings() {
      try {
        const res = await api.getUserBookings();
        this.bookings = res.bookings || [];
      } catch (err) {
        this.error = err.message || 'Failed to load booking records.';
      }
    },
    async handleCancel(booking) {
      if (!confirm(`Are you sure you want to cancel your booking for "${booking.trek_name}"?`)) return;
      
      this.cancellingId = booking.id;
      this.error = '';
      this.success = '';
      try {
        const res = await api.cancelBooking(booking.id);
        this.success = res.message || 'Booking cancelled successfully.';
        await this.fetchBookings();
      } catch (err) {
        this.error = err.message || 'Failed to cancel booking.';
      } finally {
        this.cancellingId = null;
      }
    },
    async startCsvExport() {
      this.exportLoading = true;
      this.downloadUrl = null;
      this.exportStatusMessage = 'Export job sent to background worker. Preparing your CSV file...';
      this.error = '';
      
      try {
        const res = await api.triggerCsvExport();
        const taskId = res.task_id;
        
        // Poll every 2 seconds for completion
        this.pollInterval = setInterval(async () => {
          try {
            const statusRes = await api.checkCsvExportStatus(taskId);
            if (statusRes.state === 'SUCCESS') {
              clearInterval(this.pollInterval);
              this.exportLoading = false;
              this.exportStatusMessage = '';
              this.downloadUrl = statusRes.download_url;
              this.success = `CSV export complete! Click "Download CSV File" button above to save your file (${statusRes.filename}).`;
            } else if (statusRes.state === 'FAILURE') {
              clearInterval(this.pollInterval);
              this.exportLoading = false;
              this.exportStatusMessage = '';
              this.error = 'CSV export task failed during execution.';
            } else {
              this.exportStatusMessage = `Worker Status: ${statusRes.state}... Please wait...`;
            }
          } catch (e) {
            clearInterval(this.pollInterval);
            this.exportLoading = false;
            this.exportStatusMessage = '';
            this.error = 'Error checking task status.';
          }
        }, 2000);
      } catch (err) {
        this.exportLoading = false;
        this.exportStatusMessage = '';
        this.error = err.message || 'Failed to trigger CSV export task.';
      }
    }
  },
  mounted() {
    this.fetchBookings();
  },
  beforeUnmount() {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }
};
</script>

<style scoped>
.fs-7 {
  font-size: 0.825rem;
}
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
.animate-pulse {
  animation: pulse 2s infinite;
}
</style>
