// ============================================================
// AI CAREER COPILOT - FRONTEND API CONNECTION
// ============================================================

const API_URL = window.CAREER_COPILOT_API_URL;

// ============================================================
// AUTH STORAGE KEYS
// ============================================================

const USER_STORAGE_KEY = "careerCopilotUser";
const LOGIN_STORAGE_KEY = "careerCopilotLoggedIn";
const TOKEN_STORAGE_KEY = "careerCopilotToken";

// ============================================================
// FIND LOGIN ELEMENTS
// ============================================================

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const registerUsernameInput = document.getElementById("registerUsername");
const registerPasswordInput = document.getElementById("registerPassword");
const switchAuthButton = document.getElementById("switchAuth");
const registerSubmitButton = document.getElementById("registerSubmitButton");

const buttons = document.querySelectorAll("button");

let loginButton = document.getElementById("loginButton");
let registerButton = document.getElementById("registerSubmitButton");

buttons.forEach((button) => {
    const text = button.innerText.trim().toLowerCase();
    if (!loginButton && (text.includes("enter copilot") || text.includes("login") || text.includes("sign in"))) {
        loginButton = button;
    }
    if (!registerButton && (text.includes("create new account") || text.includes("register") || text.includes("sign up"))) {
        registerButton = button;
    }
});

// ============================================================
// CHECK BACKEND CONNECTION
// ============================================================

async function checkBackendConnection() {

    try {

        const response = await fetch(
            `${API_URL}/api/status`
        );

        const result = await response.json();

        if (result.success) {

            console.log(
                "✅ Backend connected:",
                result.message
            );

            return true;
        }

        return false;

    } catch (error) {

        console.error(
            "❌ Backend connection failed:",
            error
        );

        return false;
    }
}

// ============================================================
// LOGIN
// ============================================================

async function loginUser() {

    const username = usernameInput
        ? usernameInput.value.trim()
        : "";

    const password = passwordInput
        ? passwordInput.value
        : "";

    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    if (!username || !password) {

        alert(
            "Please enter your username and password."
        );

        return;
    }

    // --------------------------------------------------------
    // DISABLE LOGIN BUTTON
    // --------------------------------------------------------

    if (loginButton) {

        loginButton.disabled = true;

        loginButton.innerText =
            "CONNECTING...";
    }

    try {

        console.log(
            "🔐 Attempting login for:",
            username
        );

        const response = await fetch(
            `${API_URL}/api/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const result = await response.json();

        console.log(
            "Login response:",
            result
        );

        // ----------------------------------------------------
        // SUCCESS
        // ----------------------------------------------------

        if (result.success) {

            const loggedInUsername =
                result.username || username;

            // ------------------------------------------------
            // DAY 38 - AUTH TOKEN VALIDATION
            // ------------------------------------------------

            if (!result.token) {

                console.error(
                    "❌ Login succeeded but authentication token was missing."
                );

                alert(
                    "Login failed: authentication token was not received."
                );

                return;
            }

            // ------------------------------------------------
            // SAVE USER SESSION
            // ------------------------------------------------

            localStorage.setItem(
                USER_STORAGE_KEY,
                loggedInUsername
            );

            localStorage.setItem(
                LOGIN_STORAGE_KEY,
                "true"
            );

            // ------------------------------------------------
            // SAVE DAY-38 AUTHENTICATION TOKEN
            // ------------------------------------------------

            localStorage.setItem(
                TOKEN_STORAGE_KEY,
                result.token
            );

            console.log(
                "🔐 Authentication token saved."
            );

            console.log(
                "👤 Logged-in user:",
                loggedInUsername
            );

            console.log(
                "⏱️ Token expires in:",
                result.expires_in,
                "seconds"
            );

            // ------------------------------------------------
            // VERIFY STORAGE BEFORE REDIRECT
            // ------------------------------------------------

            const storedUser =
                localStorage.getItem(
                    USER_STORAGE_KEY
                );

            const storedToken =
                localStorage.getItem(
                    TOKEN_STORAGE_KEY
                );

            if (!storedUser || !storedToken) {

                console.error(
                    "❌ Authentication data could not be saved to localStorage."
                );

                alert(
                    "Login failed: unable to save your authentication session."
                );

                return;
            }

            console.log(
                "✅ Authentication session stored successfully."
            );

            alert(
                `Welcome back, ${loggedInUsername}! 🚀`
            );

            // ------------------------------------------------
            // REDIRECT TO DASHBOARD
            // ------------------------------------------------

            window.location.replace(
                "dashboard.html?v=20260923"
            );

            return;
        }

        // ----------------------------------------------------
        // FAILED LOGIN
        // ----------------------------------------------------

        alert(
            result.message ||
            "Invalid username or password."
        );

    } catch (error) {

        console.error(
            "❌ Login error:",
            error
        );

        alert(
            "Unable to connect to AI Career Copilot server.\n\n" +
            "Make sure the Flask backend is running."
        );

    } finally {

        if (loginButton) {

            loginButton.disabled = false;

            loginButton.innerText =
                "ENTER COPILOT →";
        }
    }
}

// ============================================================
// REGISTER
// ============================================================

async function registerUser() {

    const username = registerUsernameInput
        ? registerUsernameInput.value.trim()
        : "";

    const password = registerPasswordInput
        ? registerPasswordInput.value.trim()
        : "";

    if (!username || !password) {
        alert("Please enter a username and password to create an account.");
        return;
    }

    try {
        console.log("📝 Registering user:", username);

        const response = await fetch(`${API_URL}/api/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const result = await response.json();
        console.log("Registration response:", result);

        if (result.success) {
            alert("✅ Account created successfully!\n\nYou can now login.");

            if (registerForm) {
                registerForm.classList.add("hidden");
            }

            if (loginForm) {
                loginForm.classList.remove("hidden");
            }

            if (switchAuthButton) {
                switchAuthButton.textContent = "Create new account";
            }

            if (usernameInput) {
                usernameInput.value = username;
            }

            if (passwordInput) {
                passwordInput.value = "";
            }

            if (registerUsernameInput) {
                registerUsernameInput.value = "";
            }

            if (registerPasswordInput) {
                registerPasswordInput.value = "";
            }
        } else {
            alert(result.message || "Registration failed.");
        }

    } catch (error) {
        console.error("❌ Registration error:", error);
        alert("Unable to connect to AI Career Copilot server.\n\nMake sure the Flask backend is running.");
    }
}

// ============================================================
// BUTTON / FORM EVENTS
// ============================================================
//
// IMPORTANT:
// The login button is likely inside an HTML <form>.
// Without preventing the form's default submission,
// the browser performs a GET request and exposes
// username/password in the URL.
//
// We intercept the form submit and run loginUser()
// through JavaScript instead.
// ============================================================

if (loginButton && loginForm) {
    loginForm.addEventListener("submit", function (event) {
        event.preventDefault();
        event.stopPropagation();
        loginUser();
    });
} else if (loginButton) {
    loginButton.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        loginUser();
    });
}

if (switchAuthButton) {
    switchAuthButton.addEventListener("click", function () {
        const showingLogin = !loginForm.classList.contains("hidden");
        if (showingLogin) {
            registerForm.classList.remove("hidden");
            loginForm.classList.add("hidden");
            switchAuthButton.textContent = "Already have an account? Login";
        } else {
            registerForm.classList.add("hidden");
            loginForm.classList.remove("hidden");
            switchAuthButton.textContent = "Create new account";
        }
    });
}

if (registerSubmitButton && registerForm) {
    registerForm.addEventListener("submit", function (event) {
        event.preventDefault();
        event.stopPropagation();
        registerUser();
    });
}

// ============================================================
// ENTER KEY LOGIN
// ============================================================

if (passwordInput) {

    passwordInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                event.preventDefault();

                event.stopPropagation();

                loginUser();
            }

        }
    );
}

// ============================================================
// PASSWORD SHOW / HIDE
// ============================================================

const passwordToggle =
    document.getElementById(
        "passwordToggle"
    );

const passwordField =
    document.getElementById(
        "password"
    );

if (
    passwordToggle &&
    passwordField
) {

    passwordToggle.addEventListener(
        "click",
        function (event) {

            event.preventDefault();

            if (
                passwordField.type ===
                "password"
            ) {

                passwordField.type =
                    "text";

                passwordToggle.innerText =
                    "◉";

            } else {

                passwordField.type =
                    "password";

                passwordToggle.innerText =
                    "◉";
            }

        }
    );
}

// ============================================================
// SYSTEM READY
// ============================================================

console.log(
    "🤖 AI Career Copilot frontend loaded."
);

console.log(
    "🔗 Backend API:",
    API_URL
);

console.log(
    "🔐 Token storage key:",
    TOKEN_STORAGE_KEY
);

// ============================================================
// CHECK BACKEND WHEN PAGE LOADS
// ============================================================

checkBackendConnection()
    .then((connected) => {

        if (connected) {

            console.log(
                "🟢 AI Career Copilot system ONLINE."
            );

        } else {

            console.warn(
                "🔴 AI Career Copilot backend OFFLINE."
            );
        }

    });