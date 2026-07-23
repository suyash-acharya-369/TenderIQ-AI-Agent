// TenderIQ AI Auth Manager
const AuthManager = {
    getToken() {
        return localStorage.getItem("tenderiq_access_token");
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
    async fetchWithAuth(url, options = {}) {
        const token = this.getToken();
        const headers = options.headers || {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        headers["Content-Type"] = "application/json";
        options.headers = headers;

        const response = await fetch(url, options);
        if (response.status === 401) {
            this.logout();
        }
        return response;
    }
};
