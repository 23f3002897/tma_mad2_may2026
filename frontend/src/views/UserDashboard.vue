<template>
  <div>
    <!-- Hero Banner -->
    <div class="hero-section bg-dark-premium text-white py-5 mb-4 shadow">
      <div class="container text-center py-3">
        <h1 class="display-5 fw-bold mb-3">Explore Spectacular Trekking Trails</h1>
        <p class="lead text-white-50 max-w-600 mx-auto mb-4">
          Discover high-altitude summits, scenic valleys, and pristine wilderness. Book your slots securely with instant confirmation.
        </p>

        <!-- Search & Filter Bar -->
        <div class="card border-0 shadow-lg rounded-4 p-3 max-w-800 mx-auto bg-white text-dark">
          <div class="row g-2 align-items-center">
            <div class="col-md-5">
              <input 
                type="text" 
                v-model="filters.search" 
                @input="fetchTreks" 
                class="form-control border-0 bg-light" 
                placeholder="Search treks, locations..." 
              />
            </div>
            <div class="col-md-3">
              <select v-model="filters.difficulty" @change="fetchTreks" class="form-select border-0 bg-light">
                <option value="All">Difficulty: All</option>
                <option value="Easy">Easy</option>
                <option value="Moderate">Moderate</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
            <div class="col-md-2">
              <select v-model="filters.status" @change="fetchTreks" class="form-select border-0 bg-light">
                <option value="Open">Status: Open</option>
                <option value="All">Status: All</option>
                <option value="Closed">Closed</option>
              </select>
            </div>
            <div class="col-md-2">
              <button @click="resetFilters" class="btn btn-outline-secondary w-100 rounded-pill">Reset</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="container pb-5">
      <Alert :message="error" type="danger" @close="error = ''" />
      <Alert :message="success" type="success" @close="success = ''" />

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="text-muted mt-2">Loading trekking routes...</p>
      </div>

      <div v-else class="row g-4">
        <div v-for="trek in treks" :key="trek.id" class="col-md-6 col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 h-100 d-flex flex-column justify-content-between overflow-hidden trek-card transition-all">
            <div>
              <div class="card-header border-0 bg-light py-3 d-flex justify-content-between align-items-center">
                <span class="badge px-3 py-2 rounded-pill" :class="difficultyBadge(trek.difficulty)">
                  {{ trek.difficulty }}
                </span>
                <span class="badge rounded-pill" :class="statusBadge(trek.status)">
                  {{ trek.status }}
                </span>
              </div>

              <div class="card-body p-4">
                <h5 class="fw-bold text-dark mb-1">{{ trek.name }}</h5>
                <p class="text-muted fs-7 mb-3">{{ trek.location }}</p>
                <p class="text-secondary fs-7 mb-3 description-clamp">{{ trek.description }}</p>

                <div class="bg-light p-3 rounded-3 mb-3 fs-7">
                  <div class="d-flex justify-content-between mb-1">
                    <span class="text-muted">Dates:</span>
                    <span class="fw-semibold">{{ trek.start_date }} to {{ trek.end_date }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-1">
                    <span class="text-muted">Duration:</span>
                    <span class="fw-semibold">{{ trek.duration_days }} Days</span>
                  </div>
                  <div class="d-flex justify-content-between">
                    <span class="text-muted">Guide:</span>
                    <span class="fw-semibold">{{ trek.assigned_staff_name }}</span>
                  </div>
                </div>

                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <span class="fs-7 text-muted block">Available Slots:</span>
                    <span class="fs-5 fw-bold" :class="trek.available_slots === 0 ? 'text-danger' : 'text-success'">
                      {{ trek.available_slots }}
                    </span>
                    <span class="text-muted fs-7"> / {{ trek.total_slots }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="card-footer bg-white p-4 border-top-0 pt-0">
              <button 
                @click="openBookingModal(trek)" 
                class="btn w-100 rounded-pill py-2 fw-bold shadow-sm"
                :class="trek.status === 'Open' && trek.available_slots > 0 ? 'btn-primary' : 'btn-secondary disabled'"
                :disabled="trek.status !== 'Open' || trek.available_slots === 0"
              >
                {{ trek.status === 'Open' && trek.available_slots > 0 ? 'Book Now' : 'Booking Closed' }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="treks.length === 0" class="col-12 text-center py-5">
          <div class="card border-0 shadow-sm rounded-4 p-5 bg-light max-w-600 mx-auto">
            <h4 class="text-muted mb-2">No Treks Found</h4>
            <p class="text-secondary fs-7 mb-3">No trekking routes match your search filters.</p>
            <button @click="resetFilters" class="btn btn-primary rounded-pill px-4 mx-auto">View All Treks</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Booking Modal -->
    <div class="modal fade" id="bookingModal" tabindex="-1" aria-labelledby="bookingModalLabel" aria-hidden="true" ref="bookingModalEl">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
          <div class="modal-header bg-dark-premium text-white py-3">
            <h5 class="modal-title fw-bold" id="bookingModalLabel">Book Trek: {{ selectedTrek?.name }}</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          
          <form @submit.prevent="confirmBooking">
            <div class="modal-body p-4">
              <Alert :message="bookingError" type="danger" @close="bookingError = ''" />

              <div class="bg-light p-3 rounded-3 mb-4">
                <div class="d-flex justify-content-between mb-1">
                  <span class="text-muted">Location:</span>
                  <span class="fw-semibold">{{ selectedTrek?.location }}</span>
                </div>
                <div class="d-flex justify-content-between mb-1">
                  <span class="text-muted">Start Date:</span>
                  <span class="fw-semibold">{{ selectedTrek?.start_date }}</span>
                </div>
                <div class="d-flex justify-content-between">
                  <span class="text-muted">Available Slots left:</span>
                  <span class="fw-bold text-success">{{ selectedTrek?.available_slots }}</span>
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">Number of Tickets to Book *</label>
                <input 
                  type="number" 
                  v-model="ticketsToBook" 
                  class="form-control form-control-lg text-center fw-bold text-primary" 
                  min="1" 
                  :max="selectedTrek?.available_slots" 
                  required 
                />
                <div class="form-text fs-7">
                  Maximum tickets you can book right now: {{ selectedTrek?.available_slots }}
                </div>
              </div>

              <div class="alert alert-info py-2 px-3 mb-0 fs-7 border-0 bg-info bg-opacity-10 text-info-emphasis">
                Note: Duplicate bookings for the same trek are not allowed by the system.
              </div>
            </div>

            <div class="modal-footer bg-light px-4 py-3">
              <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary rounded-pill px-4 fw-bold" :disabled="bookingLoading">
                <span v-if="bookingLoading" class="spinner-border spinner-border-sm me-2"></span>
                <span>Confirm Booking</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api, getToken, getUser } from '../services/api';
import Alert from '../components/Alert.vue';
import * as bootstrap from 'bootstrap';

export default {
  name: 'UserDashboard',
  components: { Alert },
  data() {
    return {
      treks: [],
      loading: true,
      error: '',
      success: '',
      filters: {
        search: '',
        difficulty: 'All',
        status: 'Open'
      },
      selectedTrek: null,
      ticketsToBook: 1,
      bookingLoading: false,
      bookingError: '',
      modalInstance: null
    };
  },
  methods: {
    difficultyBadge(diff) {
      if (diff === 'Easy') return 'bg-success text-white';
      if (diff === 'Moderate') return 'bg-warning text-dark';
      return 'bg-danger text-white';
    },
    statusBadge(status) {
      if (status === 'Open') return 'bg-success text-white';
      if (status === 'Closed') return 'bg-secondary text-white';
      return 'bg-info text-dark';
    },
    async fetchTreks() {
      this.loading = false;
      try {
        const res = await api.getPublicTreks(this.filters);
        this.treks = res.treks || [];
      } catch (err) {
        this.error = err.message || 'Failed to fetch treks.';
      }
    },
    resetFilters() {
      this.filters = {
        search: '',
        difficulty: 'All',
        status: 'Open'
      };
      this.fetchTreks();
    },
    openBookingModal(trek) {
      if (!getToken()) {
        this.$router.push({ name: 'Login', query: { redirect: '/' } });
        return;
      }
      this.selectedTrek = trek;
      this.ticketsToBook = 1;
      this.bookingError = '';
      if (!this.modalInstance && this.$refs.bookingModalEl) {
        this.modalInstance = new bootstrap.Modal(this.$refs.bookingModalEl);
      }
      this.modalInstance?.show();
    },
    async confirmBooking() {
      if (!this.selectedTrek) return;
      this.bookingLoading = true;
      this.bookingError = '';
      try {
        const res = await api.bookTrek(this.selectedTrek.id, this.ticketsToBook);
        this.success = res.message || 'Booking confirmed!';
        this.modalInstance?.hide();
        await this.fetchTreks();
      } catch (err) {
        this.bookingError = err.message || 'Booking failed.';
      } finally {
        this.bookingLoading = false;
      }
    }
  },
  mounted() {
    this.fetchTreks();
  }
};
</script>

<style scoped>
.bg-dark-premium {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}
.max-w-600 {
  max-width: 600px;
}
.max-w-800 {
  max-width: 800px;
}
.fs-7 {
  font-size: 0.825rem;
}
.description-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.trek-card:hover {
  transform: translateY(-4px);
}
.transition-all {
  transition: all 0.25s ease-in-out;
}
</style>
