// Supabase Client Configuration
const SUPABASE_URL = 'https://afotlyqwctmljhtroiyp.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_t-MFkypCJ50Dhk6izLM6Nw_eX3yShbu';

// Initialize Supabase client (non-blocking)
// Wait for supabase library to load
function initSupabase() {
  if (typeof window.supabase !== 'undefined' && typeof window.supabase.createClient === 'function') {
    window.supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    console.log('✅ Supabase client initialized');
  } else {
    console.warn('⚠️  Supabase library not loaded. Authentication features will be disabled.');
    // Set dummy supabase object to prevent errors
    window.supabase = null;
  }
}

// Try to initialize immediately
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSupabase);
} else {
  initSupabase();
}
