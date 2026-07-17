<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
      <div>
        <h2 class="fw-bold mb-1">Institute Admin Dashboard</h2>
        <p class="text-muted mb-0">System metrics, real-time booking analytics, and background tasks control.</p>
      </div>
      <div class="d-flex gap-2">
        <router-link to="/admin/treks" class="btn btn-outline-primary fw-semibold">Manage Treks</router-link>
        <router-link to="/admin/staff" class="btn btn-outline-warning fw-semibold">Manage Staff</router-link>
      </div>
    </div>

    <Alert :message="error" type="danger" @close="error = ''" />
    <Alert :message="success" type="success" @close="success = ''" />

    <!-- Metric Cards -->
    <div class="row g-3 mb-4" v-if="metrics">
      <div class="col-sm-6 col-lg-3">
        <div class="card border-0 shadow-sm rounded-4 bg-primary text-white p-3 h-100 d-flex flex-column justify-content-between">
          <div class="d-flex justify-content-between align-items-center">
            <span class="fs-6 text-white-50 fw-semibold uppercase">Total Routes</span>
          </div>
          <div class="fs-1 fw-bold mt-2">{{ metrics.total_treks }}</div>
        </div>
      </div>
      <div class="col-sm-6 col-lg-3">
        <div class="card border-0 shadow-sm rounded-4 bg-success text-white p-3 h-100 d-flex flex-column justify-content-between">
          <div class="d-flex justify-content-between align-items-center">
            <span class="fs-6 text-white-50 fw-semibold uppercase">Active Bookings</span>
          </div>
          <div class="fs-1 fw-bold mt-2">{{ metrics.total_bookings }}</div>
        </div>
      </div>
      <div class="col-sm-6 col-lg-3">
        <div class="card border-0 shadow-sm rounded-4 bg-warning text-dark p-3 h-100 d-flex flex-column justify-content-between">
          <div class="d-flex justify-content-between align-items-center">
            <span class="fs-6 opacity-75 fw-semibold uppercase">Trek Staff</span>
          </div>
          <div class="fs-1 fw-bold mt-2">{{ metrics.total_staff }}</div>
        </div>
      </div>
      <div class="col-sm-6 col-lg-3">
        <div class="card border-0 shadow-sm rounded-4 bg-info text-dark p-3 h-100 d-flex flex-column justify-content-between">
          <div class="d-flex justify-content-between align-items-center">
            <span class="fs-6 opacity-75 fw-semibold uppercase">Registered Trekkers</span>
          </div>
          <div class="fs-1 fw-bold mt-2">{{ metrics.total_users }}</div>
        </div>
      </div>
    </div>

    <!-- Chart.js Analytics Section -->
    <div class="row g-4 mb-5">
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm rounded-4 p-4 h-100">
          <h5 class="fw-bold mb-3 border-bottom pb-2">Bookings by Status</h5>
          <div class="chart-container d-flex justify-content-center align-items-center" style="position: relative; height: 280px;">
            <canvas ref="statusChartCanvas"></canvas>
          </div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card border-0 shadow-sm rounded-4 p-4 h-100">
          <h5 class="fw-bold mb-3 border-bottom pb-2">Top 5 Most Popular Treks</h5>
          <div class="chart-container d-flex justify-content-center align-items-center" style="position: relative; height: 280px;">
            <canvas ref="popularChartCanvas"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- Celery Background Tasks Control Panel -->
    <div class="card border-0 shadow-sm rounded-4 bg-light p-4 mb-4 border-start border-primary border-5">
      <div class="d-flex align-items-center justify-content-between flex-wrap gap-3">
        <div>
          <h5 class="fw-bold mb-1 d-flex align-items-center">
            <span>Celery Batch Jobs Control Center</span>
          </h5>
          <p class="text-muted fs-7 mb-0">
            Manually trigger scheduled background jobs on demand.
          </p>
        </div>
        <div class="d-flex gap-2">
          <button 
            @click="triggerJob('daily_reminders')" 
            class="btn btn-outline-primary fw-semibold shadow-sm d-flex align-items-center"
            :disabled="jobLoading === 'daily_reminders'"
          >
            <span v-if="jobLoading === 'daily_reminders'" class="spinner-border spinner-border-sm me-2"></span>
            <span>Trigger Daily Reminders</span>
          </button>
          
          <button 
            @click="triggerJob('monthly_activity_report')" 
            class="btn btn-primary fw-semibold shadow-sm d-flex align-items-center"
            :disabled="jobLoading === 'monthly_activity_report'"
          >
            <span v-if="jobLoading === 'monthly_activity_report'" class="spinner-border spinner-border-sm me-2"></span>
            <span>Generate Monthly Report</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api';
import Alert from '../components/Alert.vue';
import Chart from 'chart.js/auto';

export default {
  name: 'AdminDashboard',
  components: { Alert },
  data() {
    return {
      metrics: null,
      chartsData: null,
      error: '',
      success: '',
      jobLoading: null,
      statusChartInstance: null,
      popularChartInstance: null
    };
  },
  methods: {
    async fetchDashboardData() {
      try {
        const res = await api.getAdminStats();
        this.metrics = res.metrics;
        this.chartsData = res.charts;
        this.$nextTick(() => {
          this.renderCharts();
        });
      } catch (err) {
        this.error = err.message || 'Failed to load admin dashboard statistics.';
      }
    },
    renderCharts() {
      if (!this.chartsData) return;

      // Render Booking Status Doughnut Chart
      if (this.statusChartInstance) this.statusChartInstance.destroy();
      const statusCtx = this.$refs.statusChartCanvas?.getContext('2d');
      if (statusCtx) {
        this.statusChartInstance = new Chart(statusCtx, {
          type: 'doughnut',
          data: {
            labels: this.chartsData.booking_status.labels,
            datasets: [{
              data: this.chartsData.booking_status.data,
              backgroundColor: ['#0d6efd', '#dc3545', '#198754'],
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom' }
            }
          }
        });
      }

      // Render Popular Treks Bar Chart
      if (this.popularChartInstance) this.popularChartInstance.destroy();
      const popularCtx = this.$refs.popularChartCanvas?.getContext('2d');
      if (popularCtx) {
        this.popularChartInstance = new Chart(popularCtx, {
          type: 'bar',
          data: {
            labels: this.chartsData.popular_treks.labels,
            datasets: [{
              label: 'Total Bookings',
              data: this.chartsData.popular_treks.data,
              backgroundColor: '#0dcaf0',
              borderColor: '#0bacbe',
              borderWidth: 1,
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1 } }
            },
            plugins: {
              legend: { display: false }
            }
          }
        });
      }
    },
    async triggerJob(jobName) {
      this.jobLoading = jobName;
      this.error = '';
      this.success = '';
      try {
        const res = await api.triggerScheduledJob(jobName);
        this.success = `${res.message} (Task ID: ${res.task_id})`;
      } catch (err) {
        this.error = err.message || 'Failed to trigger scheduled job.';
      } finally {
        this.jobLoading = null;
      }
    }
  },
  mounted() {
    this.fetchDashboardData();
  },
  beforeUnmount() {
    if (this.statusChartInstance) this.statusChartInstance.destroy();
    if (this.popularChartInstance) this.popularChartInstance.destroy();
  }
};
</script>

<style scoped>
.uppercase {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.fs-7 {
  font-size: 0.825rem;
}
</style>
