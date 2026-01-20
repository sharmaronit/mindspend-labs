// Supabase Authentication Manager
// Usage: Include supabase.js before this file
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
// <script src="utils/supabase.js"></script>
// <script src="utils/auth.js"></script>

const AuthManager = {
  getSupabase: function() {
    if (!window.supabase) {
      console.error('❌ Supabase client not initialized');
      return null;
    }
    return window.supabase;
  },

  // Get current user
  getCurrentUser: async function() {
    try {
      const sb = this.getSupabase();
      if (!sb) return null;
      const { data: { user }, error } = await sb.auth.getUser();
      if (error) throw error;
      return user;
    } catch (e) {
      console.error('❌ Failed to get current user:', e);
      return null;
    }
  },

  // Get current user profile with username, first_name, etc.
  getCurrentProfile: async function() {
    try {
      const user = await this.getCurrentUser();
      if (!user) return null;

      const sb = this.getSupabase();
      if (!sb) return null;

      const { data, error } = await sb
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single();

      if (error) {
        if (error.code === 'PGRST116') {
          // No rows found - create profile
          return null;
        }
        console.error('❌ Failed to get profile:', error);
        return null;
      }
      return data;
    } catch (e) {
      console.error('❌ Error getting profile:', e);
      return null;
    }
  },

  // Register new user
  register: async function(email, password, username, firstName = '', lastName = '') {
    try {
      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      // Step 1: Create auth user
      console.log('📝 Registering user:', email);
      const { data: { user }, error: signUpError } = await sb.auth.signUp({
        email,
        password,
      });

      if (signUpError) {
        console.error('❌ Auth user creation failed:', signUpError);
        return { success: false, error: signUpError.message };
      }

      console.log('✅ Auth user created with ID:', user.id);

      // Step 2: Wait briefly for session to be established
      console.log('⏳ Waiting for session to establish...');
      const { data: { session }, error: sessionError } = await sb.auth.getSession();
      
      if (sessionError || !session) {
        console.warn('⚠️ Session not available immediately, waiting 1.5 seconds...');
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      // Step 3: Create profile with the authenticated user's ID
      console.log('👤 Creating profile for user:', user.id);
      const { error: profileError } = await sb
        .from('profiles')
        .insert([{
          id: user.id,
          email,
          username,
          first_name: firstName,
          last_name: lastName,
        }]);

      if (profileError) {
        console.error('❌ Profile creation failed:');
        console.error('   Error Code:', profileError.code);
        console.error('   Error Message:', profileError.message);
        console.error('   Error Details:', profileError);
        
        // Provide helpful error message
        let userMessage = profileError.message;
        if (profileError.message.includes('row-level security')) {
          userMessage = 'Profile creation blocked by database policy. This is likely an RLS configuration issue. Check frontend/RLS_COMPLETE_FIX.md for solution.';
        } else if (profileError.message.includes('duplicate')) {
          userMessage = 'This email is already registered.';
        }
        
        // Clean up the auth user since profile creation failed
        try {
          await sb.auth.admin.deleteUser(user.id);
          console.log('🧹 Cleaned up auth user');
        } catch (e) {
          console.warn('⚠️ Could not delete auth user:', e.message);
        }
        
        return { success: false, error: userMessage };
      }

      console.log('✅ Profile created successfully');
      console.log('✅ User registered completely');
      return { success: true, user };
    } catch (e) {
      console.error('❌ Registration error:', e.message);
      return { success: false, error: e.message };
    }
  },

  // Login user
  login: async function(email, password) {
    try {
      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { data: { user }, error } = await sb.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('❌ Login failed:', error);
        return { success: false, error: error.message };
      }

      // Get user profile
      const profile = await this.getCurrentProfile();

      // Store in localStorage for quick access
      this.storeUserData(user, profile);

      console.log('✅ User logged in successfully');
      window.dispatchEvent(new CustomEvent('authUserUpdated', { detail: { user, profile } }));
      
      return { success: true, user, profile };
    } catch (e) {
      console.error('❌ Login error:', e);
      return { success: false, error: e.message };
    }
  },

  // Logout user
  logout: async function() {
    try {
      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { error } = await sb.auth.signOut();
      if (error) throw error;
      
      this.clearCurrentUser();
      console.log('✅ User logged out');
      window.dispatchEvent(new CustomEvent('authUserCleared'));
      
      return { success: true };
    } catch (e) {
      console.error('❌ Logout error:', e);
      return { success: false, error: e.message };
    }
  },

  // Check if user is authenticated
  isAuthenticated: async function() {
    const user = await this.getCurrentUser();
    return !!user;
  },

  // Get access token
  getAccessToken: async function() {
    try {
      const sb = this.getSupabase();
      if (!sb) return null;

      const { data: { session }, error } = await sb.auth.getSession();
      if (error) throw error;
      return session?.access_token || null;
    } catch (e) {
      console.error('❌ Failed to get access token:', e);
      return null;
    }
  },

  // Change password
  changePassword: async function(currentPassword, newPassword) {
    try {
      console.log('📝 Starting password change process...');
      const sb = this.getSupabase();
      if (!sb) {
        console.error('❌ Supabase not initialized');
        return { success: false, error: 'Supabase not initialized' };
      }

      // Get current user
      const { data: { user }, error: userError } = await sb.auth.getUser();
      
      if (userError || !user) {
        console.error('❌ User not authenticated:', userError);
        return { success: false, error: 'Not authenticated. Please login again.', requiresLogin: true };
      }

      console.log(`👤 User authenticated: ${user.email}`);

      // Step 1: Verify current password by attempting to re-authenticate
      console.log('⏳ Verifying current password...');
      const { data: signInData, error: signInError } = await sb.auth.signInWithPassword({
        email: user.email,
        password: currentPassword,
      });

      if (signInError) {
        console.error('❌ Current password verification failed:', signInError.message);
        return { success: false, error: 'Current password is incorrect. Please try again.' };
      }

      console.log('✅ Current password verified successfully');

      // Step 2: Update to new password using the authenticated session
      console.log('⏳ Updating password in Supabase...');
      const { data: updateData, error: updateError } = await sb.auth.updateUser({
        password: newPassword,
      });

      if (updateError) {
        console.error('❌ Password update failed:', updateError);
        let errorMsg = updateError.message || 'Failed to update password';
        
        // Handle specific Supabase errors
        if (errorMsg.toLowerCase().includes('same')) {
          errorMsg = 'New password must be different from your current password';
        } else if (errorMsg.toLowerCase().includes('password')) {
          errorMsg = 'Password update failed. Please ensure your password meets all requirements.';
        } else if (errorMsg.toLowerCase().includes('network') || errorMsg.toLowerCase().includes('connection')) {
          errorMsg = 'Connection error. Please check your internet and try again.';
        }
        
        return { success: false, error: errorMsg };
      }

      console.log('✅ Password updated successfully in Supabase');
      console.log('✅ Your password has been changed. Please use your new password on next login.');
      
      return { 
        success: true, 
        message: 'Password updated successfully' 
      };

    } catch (e) {
      console.error('❌ Password change error:', e);
      let errorMsg = 'An unexpected error occurred';
      
      if (e.message) {
        errorMsg = e.message;
      }
      
      // Handle network errors
      if (errorMsg.toLowerCase().includes('network') || errorMsg.toLowerCase().includes('fetch')) {
        errorMsg = 'Network connection error. Please check your internet connection.';
      }
      
      return { success: false, error: errorMsg };
    }
  },

  // Update user profile
  updateProfile: async function(profileData) {
    try {
      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const user = await this.getCurrentUser();
      if (!user) {
        return { success: false, error: 'Not authenticated', requiresLogin: true };
      }

      const { error } = await sb
        .from('profiles')
        .update(profileData)
        .eq('id', user.id);

      if (error) {
        console.error('❌ Profile update failed:', error);
        return { success: false, error: error.message };
      }

      console.log('✅ Profile updated successfully');
      return { success: true };
    } catch (e) {
      console.error('❌ Update profile error:', e);
      return { success: false, error: e.message };
    }
  },

  // Reset password (send reset email)
  resetPassword: async function(email) {
    try {
      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { error } = await sb.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password.html',
      });

      if (error) {
        console.error('❌ Password reset failed:', error);
        return { success: false, error: error.message };
      }

      console.log('✅ Password reset email sent');
      return { success: true };
    } catch (e) {
      console.error('❌ Reset password error:', e);
      return { success: false, error: e.message };
    }
  },

  // Update password with reset token
  updatePasswordWithToken: async function(newPassword) {
    try {
      const sb = this.getSupabase();
      if (!sb) return { success: false, error: 'Supabase not initialized' };

      const { error } = await sb.auth.updateUser({
        password: newPassword,
      });

      if (error) {
        console.error('❌ Password update failed:', error);
        return { success: false, error: error.message };
      }

      console.log('✅ Password updated successfully');
      return { success: true };
    } catch (e) {
      console.error('❌ Update password error:', e);
      return { success: false, error: e.message };
    }
  },

  // User session management
  setCurrentUser: function(userData) {
    try {
      localStorage.setItem('auth_user', JSON.stringify(userData));
      console.log('✅ User data stored:', userData.email);
      window.dispatchEvent(new CustomEvent('authUserUpdated', { detail: userData }));
    } catch (e) {
      console.error('❌ Failed to store user data:', e);
    }
  },

  getCurrentUserLocal: function() {
    try {
      const user = localStorage.getItem('auth_user');
      if (user) {
        return JSON.parse(user);
      }
      return null;
    } catch (e) {
      console.error('❌ Failed to get user data:', e);
      return null;
    }
  },

  clearCurrentUser: function() {
    try {
      localStorage.removeItem('auth_user');
      localStorage.removeItem('userProfile');
      console.log('✅ User data cleared');
      window.dispatchEvent(new CustomEvent('authUserCleared'));
    } catch (e) {
      console.error('❌ Failed to clear user data:', e);
    }
  },

  // Store and retrieve user data from localStorage
  storeUserData: function(user, profile) {
    localStorage.setItem('currentUser', JSON.stringify(user));
    localStorage.setItem('userProfile', JSON.stringify(profile));
  },

  getCachedUserData: function() {
    const user = localStorage.getItem('currentUser');
    const profile = localStorage.getItem('userProfile');
    return {
      user: user ? JSON.parse(user) : null,
      profile: profile ? JSON.parse(profile) : null,
    };
  },

  // Authentication status
  checkAuth: function() {
    const user = this.getCurrentUserLocal();
    const isAuth = user !== null;
    console.log(isAuth ? '✅ User authenticated' : '⚠️ User not authenticated');
    return isAuth;
  },

  requireAuth: function() {
    if (!this.checkAuth()) {
      console.warn('⚠️ Authentication required, redirecting to login');
      this.redirectToLogin();
      return false;
    }
    return true;
  },

  // Redirects
  redirectToLogin: function(returnUrl = null) {
    try {
      const currentUrl = returnUrl || window.location.href;
      localStorage.setItem('auth_return_url', currentUrl);
      window.location.href = 'login.html';
    } catch (e) {
      console.error('❌ Failed to redirect to login:', e);
    }
  },

  redirectToRegister: function() {
    try {
      window.location.href = 'register.html';
    } catch (e) {
      console.error('❌ Failed to redirect to register:', e);
    }
  },

  redirectAfterLogin: function() {
    try {
      const returnUrl = localStorage.getItem('auth_return_url');
      localStorage.removeItem('auth_return_url');
      
      if (returnUrl && returnUrl !== window.location.href) {
        window.location.href = returnUrl;
      } else {
        window.location.href = 'index.html';
      }
    } catch (e) {
      console.error('❌ Failed to redirect after login:', e);
      window.location.href = 'index.html';
    }
  },

  // Delete user account
  deleteAccount: async function(password) {
    try {
      console.log('⏳ Starting complete account deletion process...');
      const sb = this.getSupabase();
      if (!sb) {
        console.error('❌ Supabase not initialized');
        return { success: false, error: 'Supabase not initialized' };
      }

      // Step 1: Get current user info
      const { data: { user }, error: userError } = await sb.auth.getUser();
      
      if (userError || !user) {
        console.error('❌ User not authenticated:', userError);
        return { success: false, error: 'Not authenticated. Please login again.', requiresLogin: true };
      }

      const userId = user.id;
      const userEmail = user.email;
      console.log(`👤 Deleting account: ${userEmail}`);

      // Step 2: Call backend API to delete account from database and Supabase
      console.log('⏳ Calling backend deletion API...');
      const token = await this.getAccessToken();
      
      try {
        const response = await fetch('/api/user/account', {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error('❌ Backend deletion failed:', errorData);
          return { success: false, error: 'Failed to delete account from backend' };
        }

        const result = await response.json();
        console.log('✅ Backend deletion successful:', result);
      } catch (e) {
        console.error('❌ Backend API call failed:', e.message);
        return { success: false, error: 'Failed to connect to deletion service' };
      }

      // Step 3: Sign out from Supabase
      console.log('⏳ Signing out from Supabase...');
      try {
        const { error: signOutError } = await sb.auth.signOut();
        
        if (signOutError) {
          console.warn('⚠️ Sign out warning:', signOutError.message);
        } else {
          console.log('✅ Signed out successfully');
        }
      } catch (e) {
        console.warn('⚠️ Error signing out:', e.message);
      }

      // Step 4: Complete local cleanup
      console.log('⏳ Clearing all local data...');
      this.clearCurrentUser();
      
      // Clear all localStorage keys
      const keysToDelete = [
        'mindspend_firstName',
        'mindspend_lastName',
        'mindspend_username',
        'mindspend_email',
        'mindspend_token',
        'mindspend_refreshToken',
        'mindspend_analysis',
        'mindspend_unified_analysis',
        'mindspend_transactions',
        'mindspend_settings'
      ];
      
      keysToDelete.forEach(key => {
        localStorage.removeItem(key);
        console.log(`  🗑️ Cleared: ${key}`);
      });
      
      // Clear sessionStorage
      sessionStorage.clear();
      console.log('✅ All local data cleared');

      console.log('✅ Account deletion completed successfully');
      return { success: true, message: 'Account deleted successfully' };

    } catch (e) {
      console.error('❌ Account deletion error:', e);
      return { success: false, error: e.message || 'An unexpected error occurred during account deletion' };
    }
  },

  // Setup auth state listener
  onAuthStateChange: function(callback) {
    const sb = this.getSupabase();
    if (!sb) {
      console.error('❌ Supabase not initialized');
      return;
    }

    sb.auth.onAuthStateChange((event, session) => {
      console.log('🔐 Auth state changed:', event, session?.user?.email);
      callback(event, session);
    });
  },

  // Initialize auth on page load
  initialize: function() {
    try {
      this.onAuthStateChange((event, session) => {
        if (event === 'SIGNED_IN' && session) {
          console.log('✅ User signed in:', session.user.email);
          this.storeUserData(session.user, null);
        } else if (event === 'SIGNED_OUT') {
          console.log('✅ User signed out');
          this.clearCurrentUser();
        }
      });

      window.dispatchEvent(new CustomEvent('authReady', { detail: { isAuthenticated: this.checkAuth() } }));
      console.log('✅ Auth manager initialized');
    } catch (e) {
      console.error('❌ Failed to initialize auth manager:', e);
    }
  }
};

// Initialize auth manager when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    AuthManager.initialize();
  });
} else {
  AuthManager.initialize();
}
