const BASE_URL = 'http://127.0.0.1:5000/api';

export function getToken() {
  return localStorage.getItem('tma_token');
}

export function getUser() {
  const userStr = localStorage.getItem('tma_user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch (e) {
    return null;
  }
}

export function setToken(token, user) {
  localStorage.setItem('tma_token', token);
  localStorage.setItem('tma_user', JSON.stringify(user));
}

export function clearToken() {
  localStorage.removeItem('tma_token');
  localStorage.removeItem('tma_user');
}

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  const response = await fetch(url, config);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data.error || data.message || `HTTP Error ${response.status}`;
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  // Auth
  login: (email, password) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  }),
  register: (email, password, full_name) => request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name })
  }),
  getProfile: () => request('/auth/profile'),
  updateProfile: (data) => request('/auth/profile', {
    method: 'PUT',
    body: JSON.stringify(data)
  }),

  // User / Public Treks & Bookings
  getPublicTreks: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.difficulty && filters.difficulty !== 'All') params.append('difficulty', filters.difficulty);
    if (filters.location) params.append('location', filters.location);
    if (filters.search) params.append('search', filters.search);
    if (filters.status && filters.status !== 'All') params.append('status', filters.status);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/treks${query}`);
  },
  bookTrek: (trek_id, tickets_booked) => request('/bookings', {
    method: 'POST',
    body: JSON.stringify({ trek_id, tickets_booked })
  }),
  getUserBookings: () => request('/bookings'),
  cancelBooking: (booking_id) => request(`/bookings/${booking_id}/cancel`, {
    method: 'POST'
  }),
  triggerCsvExport: () => request('/bookings/export-csv', {
    method: 'POST'
  }),
  checkCsvExportStatus: (task_id) => request(`/bookings/export-status/${task_id}`),

  // Admin
  getAdminStats: () => request('/admin/stats'),
  getAdminTreks: () => request('/admin/treks'),
  createTrek: (data) => request('/admin/treks', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  updateTrek: (trek_id, data) => request(`/admin/treks/${trek_id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  deleteTrek: (trek_id) => request(`/admin/treks/${trek_id}`, {
    method: 'DELETE'
  }),
  getAdminStaff: () => request('/admin/staff'),
  createStaff: (data) => request('/admin/staff', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getAdminUsers: () => request('/admin/users'),
  toggleUserActive: (user_id) => request(`/admin/users/${user_id}/toggle-active`, {
    method: 'PUT'
  }),
  triggerScheduledJob: (job_name) => request(`/admin/trigger-job/${job_name}`, {
    method: 'POST'
  }),

  // Staff
  getStaffTreks: () => request('/staff/treks'),
  updateStaffTrek: (trek_id, data) => request(`/staff/treks/${trek_id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  getStaffTrekParticipants: (trek_id) => request(`/staff/treks/${trek_id}/participants`)
};
