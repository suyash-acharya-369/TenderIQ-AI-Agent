// TenderIQ AI Auth Manager - Global JWT & Page Security Engine
const AuthManager = {
    getToken() {
        return localStorage.getItem("tenderiq_access_token");
    },
    getRefreshToken() {
        return localStorage.getItem("tenderiq_refresh_token");
    },
    setTokens(accessToken, refreshToken, user) {
        localStorage.setItem("tenderiq_access_token", accessToken);
        localStorage.setItem("tenderiq_refresh_token", refreshToken);
        localStorage.setItem("tenderiq_user", JSON.stringify(user));
    },
    getUser() {
        const u = localStorage.getItem("tenderiq_user");
        return u ? JSON.parse(u) : null;
    },
    logout() {
        localStorage.removeItem("tenderiq_access_token");
        localStorage.removeItem("tenderiq_refresh_token");
        localStorage.removeItem("tenderiq_user");
        window.location.href = "/login";
    },
    isAuthenticated() {
        return !!this.getToken();
    }
};

// Monkey-patch global window.fetch to automatically include Bearer Token for /api/v1 endpoints
const originalFetch = window.fetch;
window.fetch = async function (url, options = {}) {
    const urlStr = typeof url === 'string' ? url : url.url;

    if (urlStr.includes('/api/v1/') && !urlStr.includes('/api/v1/auth/login') && !urlStr.includes('/api/v1/auth/register')) {
        options.headers = options.headers || {};
        const token = AuthManager.getToken();
        if (token) {
            if (options.headers instanceof Headers) {
                options.headers.set("Authorization", `Bearer ${token}`);
            } else if (Array.isArray(options.headers)) {
                options.headers.push(["Authorization", `Bearer ${token}`]);
            } else {
                options.headers["Authorization"] = `Bearer ${token}`;
            }
        }
    }

    const response = await originalFetch(url, options);

    if (response.status === 401 && urlStr.includes('/api/v1/') && !urlStr.includes('/api/v1/auth/login')) {
        console.warn("[AuthManager] 401 Unauthorized encountered. Redirecting to login.");
        AuthManager.logout();
    }

    return response;
};

// Page Guard & Login Form Handler Initialization
document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;

    // Login page handler
    if (path === "/login" || path.includes("login")) {
        if (AuthManager.isAuthenticated()) {
            window.location.href = "/";
            return;
        }

        const loginForm = document.getElementById("login-form");
        if (loginForm) {
            loginForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const email = document.getElementById("email")?.value.trim();
                const password = document.getElementById("password")?.value.trim();

                if (!email || !password) return;

                const submitBtn = loginForm.querySelector("button[type='submit']");
                const originalText = submitBtn ? submitBtn.innerHTML : "";
                if (submitBtn) submitBtn.innerHTML = "Authenticating...";

                try {
                    const res = await originalFetch("/api/v1/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, password })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        AuthManager.setTokens(data.access_token, data.refresh_token, data.user);
                        window.location.href = "/";
                    } else {
                        const err = await res.json();
                        alert(`Login failed: ${err.detail || 'Invalid credentials'}`);
                    }
                } catch (err) {
                    console.error("Login error:", err);
                    alert("Network error during login authentication.");
                } finally {
                    if (submitBtn) submitBtn.innerHTML = originalText;
                }
            });
        }
    } else {
        // Protected pages check
        if (!AuthManager.isAuthenticated()) {
            console.warn("[AuthManager] Unauthenticated access to protected route. Redirecting to /login.");
            window.location.href = "/login";
        }
    }
});
