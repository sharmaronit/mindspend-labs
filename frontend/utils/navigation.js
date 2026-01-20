/* ============================================
   NAVIGATION BAR COMPONENT
   - Responsive navigation with user authentication
   - Theme toggle integration
   - Active page highlighting
   ============================================ */

const Navigation = {
    currentPage: '',
    user: null,
    isDarkMode: false,

    // Initialize navigation
    init: async function() {
        this.currentPage = this.getCurrentPageName();
        this.isDarkMode = window.location.pathname.includes('-dark');
        
        // Load user profile name BEFORE generating HTML to avoid flicker
        await this.loadUserProfileNameData();

        // Check if user is authenticated BEFORE injecting nav so we show correct state
        if (typeof AuthManager !== 'undefined') {
            this.user = await AuthManager.getCurrentUser();
            if (this.user) {
                console.log('✅ User authenticated:', this.user.email);
            }
        }
        
        // Inject navigation with correct auth state
        this.injectNav();
        
        // Set active page
        this.setActivePage();
    },

    // Get current page filename
    getCurrentPageName: function() {
        const path = window.location.pathname;
        const page = path.substring(path.lastIndexOf('/') + 1);
        return page.replace('-dark.html', '.html');
    },

    // Check if user is authenticated
    isAuthenticated: function() {
        return this.user !== null;
    },
    
    // Load user profile name data before HTML generation
    loadUserProfileNameData: async function() {
        try {
            // First try localStorage for speed
            const storedFirstName = localStorage.getItem('mindspend_firstName');
            const storedLastName = localStorage.getItem('mindspend_lastName');
            const storedUsername = localStorage.getItem('mindspend_username');
            
            if (storedFirstName && storedLastName) {
                this.displayName = storedFirstName + ' ' + storedLastName;
                console.log('✅ Navigation loaded name from localStorage:', this.displayName);
                return;
            } else if (storedFirstName) {
                this.displayName = storedFirstName;
                console.log('✅ Navigation loaded name from localStorage:', this.displayName);
                return;
            } else if (storedUsername) {
                this.displayName = storedUsername;
                console.log('✅ Navigation loaded name from localStorage:', this.displayName);
                return;
            }
            
            // Fallback: load from Supabase
            if (this.isAuthenticated() && typeof AuthManager !== 'undefined') {
                const profile = await AuthManager.getCurrentProfile();
                if (profile) {
                    if (profile.first_name && profile.last_name) {
                        this.displayName = profile.first_name + ' ' + profile.last_name;
                    } else if (profile.first_name) {
                        this.displayName = profile.first_name;
                    } else if (profile.username) {
                        this.displayName = profile.username;
                    } else if (this.user && this.user.email) {
                        this.displayName = this.user.email.split('@')[0];
                    }
                    console.log('✅ Navigation loaded profile name from Supabase:', this.displayName);
                    return;
                }
            }
            
            // Final fallback
            if (this.user && this.user.email) {
                this.displayName = this.user.email.split('@')[0];
            } else {
                this.displayName = 'Guest';
            }
        } catch (e) {
            console.error('Error loading profile name:', e);
            this.displayName = 'Guest';
        }
    },
    
    // Load user profile name from Supabase after navigation is injected
    loadUserProfileName: async function() {
        try {
            if (!this.isAuthenticated() || typeof AuthManager === 'undefined') {
                return;
            }
            
            const profile = await AuthManager.getCurrentProfile();
            if (profile) {
                var displayName = '';
                if (profile.first_name && profile.last_name) {
                    displayName = profile.first_name + ' ' + profile.last_name;
                } else if (profile.first_name) {
                    displayName = profile.first_name;
                } else if (profile.username) {
                    displayName = profile.username;
                } else if (this.user && this.user.email) {
                    displayName = this.user.email.split('@')[0];
                }
                
                if (displayName) {
                    this.displayName = displayName;
                    const navUserName = document.querySelector('.nav-user-btn .user-name');
                    if (navUserName) {
                        navUserName.textContent = displayName;
                        console.log('✅ Navigation updated profile name:', displayName);
                    }
                }
            }
        } catch (e) {
            console.error('Could not load profile name for navigation:', e);
        }
    },

    // Generate navigation HTML
    generateNavHTML: function() {
        const isAuth = this.isAuthenticated();
        // Use the pre-loaded displayName to avoid flicker
        var userName = this.displayName || (isAuth && this.user && this.user.email ? this.user.email.split('@')[0] : 'Guest');
        const themeIcon = this.isDarkMode ? '☀️' : '🌙';

        return `
            <nav class="main-nav">
                <div class="nav-container">
                    <!-- Logo/Brand -->
                    <div class="nav-brand" onclick="Navigation.goHome()" style="cursor: pointer;">
                        <svg width="28" height="28" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" class="nav-logo-svg">
                            <path d="M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm0 36c-8.84 0-16-7.16-16-16s7.16-16 16-16 16 7.16 16 16-7.16 16-16 16z" fill="#6b9080"/>
                            <path d="M24 12c-6.63 0-12 5.37-12 12s5.37 12 12 12 12-5.37 12-12-5.37-12-12-12zm0 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z" fill="#6b9080"/>
                            <path d="M24 18c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6z" fill="#6b9080"/>
                        </svg>
                        <span class="nav-title">MindSpend Labs</span>
                    </div>

                    <!-- Navigation Links -->
                    <div class="nav-links" id="navLinks">
                        <a href="index.html" data-page="index.html">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="nav-link-icon">
                                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" fill="currentColor"/>
                            </svg>
                            <span>Home</span>
                        </a>
                        <a href="analytics.html" data-page="analytics.html">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="nav-link-icon">
                                <path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z" fill="currentColor"/>
                            </svg>
                            <span>Analytics</span>
                        </a>
                        <a href="insights.html" data-page="insights.html">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="nav-link-icon">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15h4v2h-4zm0-5h4v4h-4zm0-5h4v4h-4z" fill="currentColor"/>
                            </svg>
                            <span>Insights</span>
                        </a>
                        <a href="finance-dashboard.html" data-page="finance-dashboard.html">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="nav-link-icon">
                                <path d="M20 8H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm0 4h-8v2h8v-2z" fill="currentColor"/>
                            </svg>
                            <span>Finance</span>
                        </a>
                    </div>

                    <!-- User Menu & Actions -->
                    <div class="nav-actions">
                        <!-- User Menu -->
                        ${isAuth ? `
                            <div class="nav-user-menu">
                                <button class="nav-user-btn" onclick="Navigation.toggleUserMenu()">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="user-avatar-svg">
                                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                                    </svg>
                                    <span class="user-name">${userName}</span>
                                    <span class="dropdown-arrow">▼</span>
                                </button>
                                <div class="user-dropdown" id="userDropdown">
                                    <a href="#" onclick="Navigation.viewProfile(); return false;">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                                        </svg> Profile
                                    </a>
                                    <a href="#" onclick="Navigation.viewSettings(); return false;">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.62l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.48.1.62l2.03 1.58c-.05.3-.07.62-.07.94 0 .33.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.62l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.48-.1-.62l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="currentColor"/>
                                        </svg> Settings
                                    </a>
                                    <a href="#" onclick="Navigation.viewHelp(); return false;">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="currentColor"/>
                                        </svg> Help
                                    </a>
                                    <div class="dropdown-divider"></div>
                                    <a href="#" onclick="Navigation.showLogoutModal(); return false;" class="logout-link">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" fill="currentColor"/>
                                        </svg> Logout
                                    </a>
                                </div>
                            </div>
                        ` : `
                            <button class="nav-login-btn" onclick="Navigation.goToLogin()">
                                Sign In
                            </button>
                        `}

                        <!-- Mobile Menu Toggle -->
                        <button class="nav-mobile-toggle" onclick="Navigation.toggleMobileMenu()">
                            <span></span>
                            <span></span>
                            <span></span>
                        </button>
                    </div>
                </div>
            </nav>
        `;
    },

    // Inject navigation into page
    injectNav: function() {
        // Check if nav already exists
        if (document.querySelector('.main-nav')) return;

        // Create nav element
        const navElement = document.createElement('div');
        navElement.innerHTML = this.generateNavHTML();
        
        // Insert at beginning of body
        document.body.insertBefore(navElement.firstElementChild, document.body.firstChild);

        // Add CSS
        this.injectStyles();

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-user-menu')) {
                this.closeUserMenu();
            }
        });
        
        // Listen for profile updates from any page
        window.addEventListener('profileUpdated', (e) => {
            if (e.detail) {
                console.log('📡 Navigation received profile update:', e.detail);
                var displayName = '';
                if (e.detail.firstName && e.detail.lastName) {
                    displayName = e.detail.firstName + ' ' + e.detail.lastName;
                } else if (e.detail.firstName) {
                    displayName = e.detail.firstName;
                } else if (e.detail.username) {
                    displayName = e.detail.username;
                } else if (e.detail.name) {
                    displayName = e.detail.name;
                }
                
                if (displayName) {
                    const navUserName = document.querySelector('.nav-user-btn .user-name');
                    if (navUserName) {
                        navUserName.textContent = displayName;
                        console.log('✅ Navigation updated with name:', displayName);
                    }
                }
            }
        });
    },

    // Inject navigation styles
    injectStyles: function() {
        if (document.getElementById('nav-styles')) return;

        const isDark = this.isDarkMode;
        const colors = isDark ? {
            navBg: '#2a2a2a',
            navBorder: '#444444',
            navText: '#e0e0e0',
            navTextSecondary: '#a0a0a0',
            navHoverBg: '#3a3a3a',
            navActiveBg: '#4a4a4a',
            dropdownBg: '#1a1a1a',
            buttonBg: '#3a3a3a',
            buttonHoverBg: '#4a4a4a'
        } : {
            navBg: '#ffffff',
            navBorder: '#e0ddd5',
            navText: '#2d3436',
            navTextSecondary: '#636e72',
            navHoverBg: '#f5f7fa',
            navActiveBg: '#e8f4f1',
            dropdownBg: '#ffffff',
            buttonBg: '#6b9080',
            buttonHoverBg: '#5a7d6f'
        };

        const styles = `
            <style id="nav-styles">
                @keyframes navFadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(-5px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .main-nav {
                    background: ${colors.navBg};
                    border-bottom: 2px solid ${colors.navBorder};
                    padding: 0;
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    background: ${isDark ? 'rgba(42, 42, 42, 0.45)' : 'rgba(255, 255, 255, 0.45)'};
                    animation: navFadeIn 0.3s ease-out;
                }

                .nav-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 24px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    height: 70px;
                }

                .nav-brand {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-weight: 600;
                    color: ${colors.navText};
                    font-size: 20px;
                }

                .nav-logo-svg {
                    transition: transform 0.3s ease;
                }

                .nav-brand:hover .nav-logo-svg {
                    transform: scale(1.1);
                }

                .nav-title {
                    font-family: 'Sora', sans-serif;
                }

                .nav-links {
                    display: flex;
                    gap: 8px;
                    flex: 1;
                    justify-content: center;
                }

                .nav-links a {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 20px;
                    color: ${colors.navText};
                    text-decoration: none;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    font-size: 15px;
                }

                .nav-links a:hover {
                    background: ${colors.navHoverBg};
                }

                .nav-links a.active {
                    background: ${colors.navActiveBg};
                    color: ${isDark ? '#51cf66' : '#4d7464'};
                    font-weight: 600;
                }

                .nav-link-icon {
                    color: currentColor;
                    transition: color 0.3s ease;
                }

                .nav-actions {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                }

                .nav-theme-toggle {
                    background: transparent;
                    border: 2px solid ${colors.navBorder};
                    border-radius: 50%;
                    width: 45px;
                    height: 45px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    font-size: 20px;
                    transition: all 0.3s ease;
                }

                .nav-theme-toggle:hover {
                    transform: rotate(20deg) scale(1.1);
                    border-color: ${isDark ? '#585858' : '#6b9080'};
                }

                .nav-user-menu {
                    position: relative;
                }

                .nav-user-btn {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 8px 16px;
                    background: ${colors.buttonBg};
                    color: ${isDark ? '#e0e0e0' : '#ffffff'};
                    border: none;
                    border-radius: 25px;
                    cursor: pointer;
                    font-family: 'Sora', sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }

                .nav-user-btn:hover {
                    background: ${colors.buttonHoverBg};
                    transform: translateY(-1px);
                }

                .user-avatar-svg {
                    color: ${isDark ? '#e0e0e0' : '#ffffff'};
                }

                .user-name {
                    max-width: 150px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }

                .dropdown-arrow {
                    font-size: 10px;
                    transition: transform 0.3s ease;
                }

                .nav-user-btn.open .dropdown-arrow {
                    transform: rotate(180deg);
                }

                .user-dropdown {
                    position: absolute;
                    top: calc(100% + 8px);
                    right: 0;
                    background: ${colors.dropdownBg};
                    border: 2px solid ${colors.navBorder};
                    border-radius: 12px;
                    padding: 8px;
                    min-width: 200px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    display: none;
                    animation: dropdownSlide 0.2s ease;
                }

                @keyframes dropdownSlide {
                    from {
                        opacity: 0;
                        transform: translateY(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .user-dropdown.show {
                    display: block;
                }

                .user-dropdown a {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 10px 14px;
                    color: ${colors.navText};
                    text-decoration: none;
                    border-radius: 6px;
                    transition: background 0.2s ease;
                    font-size: 14px;
                }

                .user-dropdown a:hover {
                    background: ${colors.navHoverBg};
                }

                .user-dropdown a.logout-link {
                    color: ${isDark ? '#ff6b6b' : '#d63031'};
                }

                .dropdown-divider {
                    height: 1px;
                    background: ${colors.navBorder};
                    margin: 8px 0;
                }

                .nav-login-btn {
                    padding: 10px 24px;
                    background: ${colors.buttonBg};
                    color: ${isDark ? '#e0e0e0' : '#ffffff'};
                    border: none;
                    border-radius: 25px;
                    cursor: pointer;
                    font-family: 'Sora', sans-serif;
                    font-size: 14px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                }

                .nav-login-btn:hover {
                    background: ${colors.buttonHoverBg};
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                }

                .nav-mobile-toggle {
                    display: none;
                    flex-direction: column;
                    gap: 5px;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    padding: 8px;
                }

                .nav-mobile-toggle span {
                    width: 25px;
                    height: 3px;
                    background: ${colors.navText};
                    border-radius: 2px;
                    transition: all 0.3s ease;
                }

                /* Mobile Responsive */
                @media (max-width: 768px) {
                    .nav-container {
                        padding: 0 16px;
                        height: 60px;
                    }

                    .nav-brand {
                        font-size: 18px;
                    }

                    .nav-logo {
                        font-size: 24px;
                    }

                    .nav-links {
                        position: fixed;
                        top: 60px;
                        left: 0;
                        right: 0;
                        background: ${colors.navBg};
                        flex-direction: column;
                        padding: 16px;
                        gap: 4px;
                        border-bottom: 2px solid ${colors.navBorder};
                        display: none;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }

                    .nav-links.show {
                        display: flex;
                    }

                    .nav-links a {
                        width: 100%;
                        padding: 14px 16px;
                    }

                    .nav-mobile-toggle {
                        display: flex;
                    }

                    .nav-theme-toggle {
                        width: 40px;
                        height: 40px;
                        font-size: 18px;
                    }

                    .user-name {
                        display: none;
                    }

                    .nav-user-btn {
                        padding: 8px 12px;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    },

    // Set active page in navigation
    setActivePage: function() {
        const links = document.querySelectorAll('.nav-links a');
        links.forEach(link => {
            const linkPage = link.getAttribute('data-page');
            if (linkPage === this.currentPage) {
                link.classList.add('active');
            }
        });
    },

    // Toggle user dropdown menu
    toggleUserMenu: function() {
        const dropdown = document.getElementById('userDropdown');
        const btn = document.querySelector('.nav-user-btn');
        
        if (dropdown) {
            dropdown.classList.toggle('show');
            btn.classList.toggle('open');
        }
    },

    // Close user dropdown menu
    closeUserMenu: function() {
        const dropdown = document.getElementById('userDropdown');
        const btn = document.querySelector('.nav-user-btn');
        
        if (dropdown) {
            dropdown.classList.remove('show');
            btn?.classList.remove('open');
        }
    },

    // Toggle mobile menu
    toggleMobileMenu: function() {
        const navLinks = document.getElementById('navLinks');
        navLinks.classList.toggle('show');
    },

    // Toggle theme
    // Navigation actions
    goHome: function() {
        window.location.href = 'index.html';
    },

    goToLogin: function() {
        const themeSuffix = this.isDarkMode ? '-dark' : '';
        window.location.href = `login${themeSuffix}.html`;
    },

    viewProfile: function() {
        const themeSuffix = this.isDarkMode ? '-dark' : '';
        window.location.href = `profile${themeSuffix}.html`;
    },

    viewSettings: function() {
        const themeSuffix = this.isDarkMode ? '-dark' : '';
        window.location.href = `settings${themeSuffix}.html`;
    },

    showLogoutModal: function() {
        this.closeUserMenu();
        
        // Create modal if it doesn't exist
        let modal = document.getElementById('logoutModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'logoutModal';
            modal.innerHTML = `
                <div class="logout-modal-overlay" onclick="Navigation.closeLogoutModal()">
                    <div class="logout-modal" onclick="event.stopPropagation()">
                        <div class="logout-modal-header">
                            <h2>Confirm Logout</h2>
                            <button class="logout-modal-close" onclick="Navigation.closeLogoutModal()">&times;</button>
                        </div>
                        <div class="logout-modal-body">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="logout-icon">
                                <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" fill="#d63031"/>
                            </svg>
                            <p class="logout-modal-text">Are you sure you want to logout from MindSpend?</p>
                            <p class="logout-modal-subtext">You'll need to sign in again to access your account.</p>
                        </div>
                        <div class="logout-modal-footer">
                            <button class="logout-modal-btn cancel" onclick="Navigation.closeLogoutModal()">Cancel</button>
                            <button class="logout-modal-btn confirm" onclick="Navigation.confirmLogout()">Logout</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            this.addLogoutModalStyles();
        }
        
        // Show modal
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    },

    closeLogoutModal: function() {
        const modal = document.getElementById('logoutModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    },

    confirmLogout: async function() {
        Navigation.closeLogoutModal();
        
        try {
            // Call Supabase logout
            if (typeof AuthManager !== 'undefined') {
                const result = await AuthManager.logout();
                if (!result.success) {
                    console.warn('Logout warning:', result.error);
                }
            }
            
            // Clear localStorage
            localStorage.clear();
            
            // Redirect to login
            Navigation.goToLogin();
        } catch (e) {
            console.error('Logout error:', e);
            // Force redirect even if logout fails
            Navigation.goToLogin();
        }
    },

    addLogoutModalStyles: function() {
        if (document.getElementById('logoutModalStyles')) return;
        
        const style = document.createElement('style');
        style.id = 'logoutModalStyles';
        style.textContent = `
            #logoutModal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            }

            .logout-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
            }

            .logout-modal {
                position: relative;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 420px;
                width: 90%;
                animation: modalSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                overflow: hidden;
            }

            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: scale(0.95) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
            }

            .logout-modal-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 24px 24px 16px 24px;
                border-bottom: 1px solid #e0ddd5;
            }

            .logout-modal-header h2 {
                margin: 0;
                font-size: 20px;
                font-weight: 700;
                color: #2d3436;
                font-family: 'Sora', sans-serif;
            }

            .logout-modal-close {
                background: none;
                border: none;
                font-size: 28px;
                color: #636e72;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: all 0.2s ease;
            }

            .logout-modal-close:hover {
                background: #f5f3f0;
                color: #2d3436;
            }

            .logout-modal-body {
                padding: 32px 24px;
                text-align: center;
            }

            .logout-icon {
                margin-bottom: 16px;
                animation: logoutIconPulse 0.6s ease-in-out;
            }

            @keyframes logoutIconPulse {
                0% { opacity: 0; transform: scale(0.8); }
                50% { opacity: 1; }
                100% { opacity: 1; transform: scale(1); }
            }

            .logout-modal-text {
                margin: 0 0 8px 0;
                font-size: 16px;
                font-weight: 600;
                color: #2d3436;
                font-family: 'Sora', sans-serif;
            }

            .logout-modal-subtext {
                margin: 0;
                font-size: 14px;
                color: #636e72;
                font-family: 'Sora', sans-serif;
                line-height: 1.5;
            }

            .logout-modal-footer {
                display: flex;
                gap: 12px;
                padding: 16px 24px 24px 24px;
                border-top: 1px solid #e0ddd5;
            }

            .logout-modal-btn {
                flex: 1;
                padding: 12px 20px;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                font-family: 'Sora', sans-serif;
                transition: all 0.3s ease;
            }

            .logout-modal-btn.cancel {
                background: #f5f3f0;
                color: #636e72;
                border: 2px solid #e0ddd5;
            }

            .logout-modal-btn.cancel:hover {
                background: #ece9e2;
                border-color: #d4d1c9;
            }

            .logout-modal-btn.confirm {
                background: #d63031;
                color: white;
                box-shadow: 0 4px 12px rgba(214, 48, 49, 0.3);
            }

            .logout-modal-btn.confirm:hover {
                background: #c92a2a;
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(214, 48, 49, 0.4);
            }

            .logout-modal-btn.confirm:active {
                transform: translateY(0);
            }
        `;
        document.head.appendChild(style);
    },

    logout: async function() {
        this.showLogoutModal();
    },

    viewHelp: function() {
        this.closeUserMenu();
        // Navigate to help page
        window.location.href = 'help.html';
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Navigation.init());
} else {
    Navigation.init();
}
