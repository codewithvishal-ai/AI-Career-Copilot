(() => {
    const configuredApiUrl = window.CAREER_COPILOT_API_URL;
    const isLocalFrontend =
        ["localhost", "127.0.0.1"].includes(window.location.hostname) &&
        ["5500", "8000"].includes(window.location.port);
    const apiBaseUrl = configuredApiUrl || (
        isLocalFrontend
            ? "http://127.0.0.1:5000"
            : window.location.origin
    );

    window.CAREER_COPILOT_API_URL = apiBaseUrl.replace(/\/+$/, "");
})();
