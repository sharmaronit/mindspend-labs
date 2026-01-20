// Unified Storage Manager - Shared across all light/dark modes
const StorageManager = {
  KEY: 'mindspend_unified_analysis',
  
  save: function(data) {
    try {
      localStorage.setItem(StorageManager.KEY, JSON.stringify(data));
      console.log('✅ Data saved to storage:', data);
      // Sync across all open tabs
      window.dispatchEvent(new CustomEvent('storageUpdated', { detail: data }));
    } catch (e) {
      console.error('❌ Storage save error:', e);
    }
  },
  
  load: function() {
    try {
      const data = localStorage.getItem(StorageManager.KEY);
      if (data) {
        const parsed = JSON.parse(data);
        console.log('✅ Data loaded from storage:', parsed);
        return parsed;
      }
      console.warn('⚠️  No data found in storage');
      return null;
    } catch (e) {
      console.error('❌ Storage load error:', e);
      return null;
    }
  },
  
  clear: function() {
    try {
      localStorage.removeItem(StorageManager.KEY);
      console.log('✅ Storage cleared');
      window.dispatchEvent(new CustomEvent('storageCleared'));
    } catch (e) {
      console.error('❌ Storage clear error:', e);
    }
  },
  
  exists: function() {
    return localStorage.getItem(StorageManager.KEY) !== null;
  }
};

// Sync data across tabs
window.addEventListener('storage', function(e) {
  if (e.key === StorageManager.KEY) {
    console.log('📡 Storage synced from another tab');
    window.dispatchEvent(new CustomEvent('storageUpdated', { detail: JSON.parse(e.newValue) }));
  }
});
