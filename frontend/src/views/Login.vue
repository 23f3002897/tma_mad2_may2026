<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-4 overflow-hidden">
          <div class="card-header bg-dark-premium text-white text-center py-4">
            <h3 class="mb-0 fw-bold">Welcome Back</h3>
            <p class="mb-0 text-white-50 fs-7">Login to Trekking Management System</p>
          </div>
          
          <div class="card-body p-4 p-md-5">
            <Alert :message="error" type="danger" @close="error = ''" />

            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label class="form-label fw-semibold">Email Address</label>
                <input 
                  type="email" 
                  v-model="email" 
                  class="form-control" 
                  placeholder="Enter email..." 
                  required 
                  autofocus
                />
              </div>

              <div class="mb-4">
                <label class="form-label fw-semibold">Password</label>
                <input 
                  type="password" 
                  v-model="password" 
                  class="form-control" 
                  placeholder="Enter password..." 
                  required
                />
              </div>

              <button type="submit" class="btn btn-primary w-100 py-2 rounded-pill fw-bold shadow-sm mb-3" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                <span>{{ loading ? 'Logging in...' : 'Login' }}</span>
              </button>
            </form>

            <div class="text-center mt-3">
              <span class="text-muted fs-7">Don't have an account?</span>
              <router-link to="/register" class="text-decoration-none fw-bold ms-1">Register Now</router-link>
            </div>

            <!-- Quick Login Helpers -->
            <hr class="my-4 text-muted opacity-25">
            <div class="bg-light p-3 rounded-3 border">
              <p class="fs-7 fw-bold text-muted mb-2 text-center">Quick Fill Credentials:</p>
              <div class="d-flex justify-content-between gap-1">
                <button @click.prevent="fillCredentials('admin@tma.com', 'admin123')" class="btn btn-outline-danger btn-sm flex-fill py-1 fs-7">
                  Admin
                </button>
                <button @click.prevent="fillCredentials('staff@tma.com', 'staff123')" class="btn btn-outline-warning btn-sm flex-fill py-1 fs-7">
                  Staff Guide
                </button>
                <button @click.prevent="fillCredentials('user@tma.com', 'user123')" class="btn btn-outline-info btn-sm flex-fill py-1 fs-7">
                  Trekker
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api, setToken } from '../services/api';
import Alert from '../components/Alert.vue';

export default {
  name: 'Login',
  components: { Alert },
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: ''
    };
  },
  methods: {
    fillCredentials(email, pwd) {
      this.email = email;
      this.password = pwd;
      this.error = '';
    },
    async handleLogin() {
      this.loading = true;
      this.error = '';
      try {
        const res = await api.login(this.email, this.password);
        setToken(res.token, res.user);
        window.dispatchEvent(new Event('auth-change'));

        // Redirect based on role or intended destination
        const redirect = this.$route.query.redirect;
        if (redirect) {
          this.$router.push(redirect);
        } else if (res.user.role === 'admin') {
          this.$router.push('/admin');
        } else if (res.user.role === 'staff') {
          this.$router.push('/staff');
        } else {
          this.$router.push('/');
        }
      } catch (err) {
        this.error = err.message || 'Login failed. Please verify credentials.';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.bg-dark-premium {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}
.fs-7 {
  font-size: 0.8rem;
}
</style>
