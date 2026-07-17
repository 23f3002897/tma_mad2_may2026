<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-4 overflow-hidden">
          <div class="card-header bg-primary text-white text-center py-4">
            <h3 class="mb-0 fw-bold">Join TMA Today</h3>
            <p class="mb-0 text-white-50 fs-7">Create your Trekker account</p>
          </div>
          
          <div class="card-body p-4 p-md-5">
            <Alert :message="error" type="danger" @close="error = ''" />
            <Alert :message="success" type="success" :dismissible="false" />

            <form @submit.prevent="handleRegister" v-if="!success">
              <div class="mb-3">
                <label class="form-label fw-semibold">Full Name</label>
                <input 
                  type="text" 
                  v-model="fullName" 
                  class="form-control" 
                  placeholder="e.g. Rahul Sharma" 
                  required 
                  autofocus
                />
              </div>

              <div class="mb-3">
                <label class="form-label fw-semibold">Email Address</label>
                <input 
                  type="email" 
                  v-model="email" 
                  class="form-control" 
                  placeholder="e.g. rahul@example.com" 
                  required
                />
              </div>

              <div class="mb-4">
                <label class="form-label fw-semibold">Password (min 6 chars)</label>
                <input 
                  type="password" 
                  v-model="password" 
                  class="form-control" 
                  placeholder="Create a strong password..." 
                  required 
                  minlength="6"
                />
              </div>

              <button type="submit" class="btn btn-primary w-100 py-2 rounded-pill fw-bold shadow-sm mb-3" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span>{{ loading ? 'Registering...' : 'Create Account' }}</span>
              </button>
            </form>

            <div class="text-center mt-3">
              <span class="text-muted fs-7">Already have an account?</span>
              <router-link to="/login" class="text-decoration-none fw-bold ms-1">Login Here</router-link>
            </div>

            <div class="alert alert-info mt-4 mb-0 fs-7 py-2 text-center border-0 bg-info bg-opacity-10 text-info-emphasis">
              Note: Only Trekkers can self-register. Trek Staff accounts must be created by Institute Admins.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api';
import Alert from '../components/Alert.vue';

export default {
  name: 'Register',
  components: { Alert },
  data() {
    return {
      fullName: '',
      email: '',
      password: '',
      loading: false,
      error: '',
      success: ''
    };
  },
  methods: {
    async handleRegister() {
      this.loading = true;
      this.error = '';
      this.success = '';
      try {
        const res = await api.register(this.email, this.password, this.fullName);
        this.success = res.message || 'Registration successful! Redirecting to login...';
        setTimeout(() => {
          this.$router.push('/login');
        }, 1500);
      } catch (err) {
        this.error = err.message || 'Registration failed.';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.fs-7 {
  font-size: 0.8rem;
}
</style>
