// Quick RLS Policy Debug Helper
// Add this to browser console to test and debug RLS issues

const RLSDebug = {
  // Test 1: Check if Supabase is initialized
  testSupabaseInit: async function() {
    console.log('🔍 Test 1: Supabase Initialization');
    if (!window.supabase) {
      console.error('❌ Supabase not initialized');
      return false;
    }
    console.log('✅ Supabase initialized');
    return true;
  },

  // Test 2: Check current user
  testCurrentUser: async function() {
    console.log('🔍 Test 2: Current User');
    const { data: { user }, error } = await window.supabase.auth.getUser();
    if (error) {
      console.error('❌ Error getting user:', error);
      return null;
    }
    if (!user) {
      console.warn('⚠️  No authenticated user');
      return null;
    }
    console.log('✅ User:', user.email, 'ID:', user.id);
    return user;
  },

  // Test 3: Check profiles table access
  testProfilesAccess: async function() {
    console.log('🔍 Test 3: Profiles Table Access');
    const { data, error } = await window.supabase
      .from('profiles')
      .select('*')
      .limit(1);
    
    if (error) {
      console.error('❌ Error reading profiles:', error);
      return false;
    }
    console.log('✅ Can read profiles table');
    return true;
  },

  // Test 4: Try to read own profile
  testOwnProfile: async function() {
    console.log('🔍 Test 4: Read Own Profile');
    const user = await this.testCurrentUser();
    if (!user) {
      console.error('❌ No user to test with');
      return false;
    }

    const { data, error } = await window.supabase
      .from('profiles')
      .select('*')
      .eq('id', user.id)
      .single();
    
    if (error) {
      console.error('❌ Error reading own profile:', error);
      return false;
    }
    console.log('✅ Own profile:', data);
    return true;
  },

  // Test 5: Try to create a test record
  testInsertProfile: async function() {
    console.log('🔍 Test 5: Insert Test Profile');
    const user = await this.testCurrentUser();
    if (!user) {
      console.error('❌ No user to test with');
      return false;
    }

    const { data, error } = await window.supabase
      .from('profiles')
      .insert([{
        id: user.id,
        email: user.email,
        username: 'test_' + Date.now(),
      }])
      .select();
    
    if (error) {
      console.error('❌ Error inserting profile:', error.message);
      console.error('Error code:', error.code);
      console.error('Error details:', error);
      return false;
    }
    console.log('✅ Successfully inserted:', data);
    return true;
  },

  // Test 6: Check RLS policies
  testRLSPolicies: async function() {
    console.log('🔍 Test 6: RLS Policies');
    console.log('Note: This requires service role access, checking from frontend...');
    
    // We can't directly query policies from frontend, but we can test RLS by attempting operations
    const tests = [
      { name: 'Read own profile', fn: () => this.testOwnProfile() },
      { name: 'Insert record', fn: () => this.testInsertProfile() },
    ];

    for (const test of tests) {
      const result = await test.fn();
      console.log(result ? `✅ ${test.name}` : `❌ ${test.name}`);
    }
  },

  // Run all tests
  runAll: async function() {
    console.log('===== RLS DEBUG TESTS =====\n');
    
    await this.testSupabaseInit();
    console.log('');
    
    await this.testCurrentUser();
    console.log('');
    
    await this.testProfilesAccess();
    console.log('');
    
    await this.testOwnProfile();
    console.log('');
    
    await this.testRLSPolicies();
    console.log('\n===== TESTS COMPLETE =====');
  }
};

// Usage: Copy to browser console and run:
// RLSDebug.runAll()
// OR test individual functions:
// RLSDebug.testCurrentUser()
// RLSDebug.testOwnProfile()
// RLSDebug.testInsertProfile()
