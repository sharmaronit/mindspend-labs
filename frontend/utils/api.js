// Supabase API Client Wrapper
// Handles database operations using Supabase client
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
// <script src="utils/supabase.js"></script>
// <script src="utils/auth.js"></script>
// <script src="utils/api.js"></script>

window.API = {
  getSupabase: function() {
    if (!window.supabase) {
      console.error('❌ Supabase client not initialized');
      return null;
    }
    return window.supabase;
  },

  // Get user profile
  getProfile: async function() {
    try {
      const user = await AuthManager.getCurrentUser();
      if (!user) {
        return { success: false, error: 'Not authenticated' };
      }
      const profile = await AuthManager.getCurrentProfile();
      if (!profile) {
        return { success: false, error: 'Profile not found' };
      }
      return { success: true, user: { ...user, ...profile } };
    } catch (e) {
      console.error('❌ Failed to get profile:', e);
      return { success: false, error: e.message };
    }
  },

  // Get user profile (alias)
  getUserProfile: async function() {
    try {
      const profile = await AuthManager.getCurrentProfile();
      if (!profile) {
        return { success: false, error: 'Profile not found' };
      }
      return { success: true, data: profile };
    } catch (e) {
      console.error('❌ Failed to get profile:', e);
      return { success: false, error: e.message };
    }
  },

  // Update user profile
  updateUserProfile: async function(profileData) {
    try {
      const result = await AuthManager.updateProfile(profileData);
      return result;
    } catch (e) {
      console.error('❌ Failed to update profile:', e);
      return { success: false, error: e.message };
    }
  },

  // Change password
  changePassword: async function(currentPassword, newPassword) {
    try {
      const result = await AuthManager.changePassword(currentPassword, newPassword);
      return result;
    } catch (e) {
      console.error('❌ Failed to change password:', e);
      return { success: false, error: e.message };
    }
  },

  // Reset password
  requestPasswordReset: async function(email) {
    try {
      const result = await AuthManager.resetPassword(email);
      return result;
    } catch (e) {
      console.error('❌ Failed to request password reset:', e);
      return { success: false, error: e.message };
    }
  },

  // Update password with reset token
  updatePasswordWithToken: async function(newPassword) {
    try {
      const result = await AuthManager.updatePasswordWithToken(newPassword);
      return result;
    } catch (e) {
      console.error('❌ Failed to update password:', e);
      return { success: false, error: e.message };
    }
  },

  // Get user metrics
  getMetrics: async function() {
    try {
      const user = await AuthManager.getCurrentUser();
      if (!user) {
        return { success: false, error: 'Not authenticated', requiresLogin: true };
      }

      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { data, error } = await sb
        .from('metrics')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('❌ Failed to get metrics:', error);
        return { success: false, error: error.message };
      }

      return { success: true, data };
    } catch (e) {
      console.error('❌ Error getting metrics:', e);
      return { success: false, error: e.message };
    }
  },

  // Add metric
  addMetric: async function(metricData) {
    try {
      const user = await AuthManager.getCurrentUser();
      if (!user) {
        return { success: false, error: 'Not authenticated', requiresLogin: true };
      }

      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { data, error } = await sb
        .from('metrics')
        .insert([{
          user_id: user.id,
          category: metricData.category,
          value: metricData.value,
          description: metricData.description,
        }])
        .select();

      if (error) {
        console.error('❌ Failed to add metric:', error);
        return { success: false, error: error.message };
      }

      console.log('✅ Metric added successfully');
      return { success: true, data: data[0] };
    } catch (e) {
      console.error('❌ Error adding metric:', e);
      return { success: false, error: e.message };
    }
  },

  // Delete metric
  deleteMetric: async function(metricId) {
    try {
      const user = await AuthManager.getCurrentUser();
      if (!user) {
        return { success: false, error: 'Not authenticated', requiresLogin: true };
      }

      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { error } = await sb
        .from('metrics')
        .delete()
        .eq('id', metricId)
        .eq('user_id', user.id);

      if (error) {
        console.error('❌ Failed to delete metric:', error);
        return { success: false, error: error.message };
      }

      console.log('✅ Metric deleted successfully');
      return { success: true };
    } catch (e) {
      console.error('❌ Error deleting metric:', e);
      return { success: false, error: e.message };
    }
  }
};

// Also create const reference for compatibility
const API = window.API;

console.log('✅ API module loaded successfully');
