<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-md-8 col-lg-6">
        <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
          <div class="card-header bg-dark-premium text-white py-4 text-center">
            <h3 class="mb-0 fw-bold">My Profile & Settings</h3>
            <p class="mb-0 text-white-50 fs-7">Update your personal account information and password</p>
          </div>

          <div class="card-body p-4 p-md-5" v-if="user">
            <Alert :message="error" type="danger" @close="error = ''" />
            <Alert :message="success" type="success" @close="success = ''" />

            <form @submit.prevent="saveProfile">
              <div class="mb-3">
                <label class="form-label fw-semibold">Role & Account Type</label>
                <input type="text" :value="user.role.toUpperCase()" class="form-control bg-light fw-bold" disabled />
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">Email Address (Read-Only)</label>
                <input type="email" :value="user.email" class="form-control bg-light" disabled />
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">Full Name *</label>
                <input type="text" v-model="form.full_name" class="form-control" required />
              </div>

              <!-- Staff Specific Fields -->
              <template v-if="user.role === 'staff'">
                <div class="mb-3">
                  <label class="form-label fw-semibold">Contact Phone</label>
                  <input type="text" v-model="form.phone" class="form-control" placeholder="e.g. 9876543210" />
                </div>
                <div class="mb-3">
                  <label class="form-label fw-semibold">Specialization / Expertise</label>
                  <input type="text" v-model="form.specialization" class="form-control" placeholder="e.g. High Altitude Guide" />
                </div>
              </template>

              <hr class="my-4 text-muted opacity-25">
              <h6 class="fw-bold mb-3">Change Password (Leave blank to keep current)</h6>

              <div class="mb-4">
                <label class="form-label fw-semibold">New Password</label>
                <input type="password" v-model="form.password" class="form-control" placeholder="Enter new password (min 6 chars)..." minlength="6" />
              </div>

              <button type="submit" class="btn btn-primary w-100 py-2 rounded-pill fw-bold shadow-sm" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span>Save Profile Changes</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api, getUser, setToken, getToken } from '../services/api';
import Alert from '../components/Alert.vue';

export default {
  name: 'Profile',
  components: { Alert },
  data() {
    return {
      user: null,
      loading: false,
      error: '',
      success: '',
      form: {
        full_name: '',
        password: '',
        phone: '',
        specialization: ''
      }
    };
  },
  methods: {
    async fetchProfile() {
      try {
        const res = await api.getProfile();
        this.user = res.user || getUser();
        this.form.full_name = this.user.full_name || '';
        if (this.user.role === 'staff') {
          this.form.phone = this.user.phone || '';
          this.form.specialization = this.user.specialization || '';
        }
      } catch (err) {
        this.error = err.message || 'Failed to fetch profile info.';
      }
    },
    async saveProfile() {
      this.loading = true;
      this.error = '';
      this.success = '';
      try {
        const payload = { full_name: this.form.full_name };
        if (this.form.password) payload.password = this.form.password;
        if (this.user.role === 'staff') {
          payload.phone = this.form.phone;
          payload.specialization = this.form.specialization;
        }

        const res = await api.updateProfile(payload);
        this.user = res.user;
        setToken(getToken(), res.user);
        window.dispatchEvent(new Event('auth-change'));
        this.success = res.message || 'Profile updated successfully!';
        this.form.password = '';
      } catch (err) {
        this.error = err.message || 'Failed to update profile.';
      } finally {
        this.loading = false;
      }
    }
  },
  mounted() {
    this.fetchProfile();
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
