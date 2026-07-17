<template>
  <div id="app-wrapper" class="d-flex flex-column min-vh-100">
    <Navbar />
    
    <main class="flex-grow-1">
      <router-view />
    </main>

    <footer class="bg-dark text-white-50 py-4 mt-5 border-top border-secondary border-opacity-25">
      <div class="container text-center fs-7">
        <p class="mb-1 fw-bold text-white">Trekking Management Application (TMA)</p>
        <p class="mb-0">
          Powered by Flask, Celery, Redis, Vue 3 & Bootstrap 5
        </p>
      </div>
    </footer>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue';

export default {
  name: 'App',
  components: {
    Navbar
  }
}
</script>

<style>
/* Global overrides and layout helpers */
#app-wrapper {
  background-color: #f8fafc;
  color: #1e293b;
}
</style>
