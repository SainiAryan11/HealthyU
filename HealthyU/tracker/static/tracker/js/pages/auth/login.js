document.addEventListener("DOMContentLoaded", () => {
    // ---------- Elements ----------
    const form = document.getElementById("loginForm");
    const emailInput = document.getElementById("emailInput");
    const passwordInput = document.getElementById("passwordInput");

    const toggleBtn = document.getElementById("togglePasswordBtn"); // add this id on your button
    const eyeIcon = document.getElementById("eyeIcon");             // svg element that holds <path> etc.

    // ---------- Password Toggle ----------
    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener("click", () => {
        const isPassword = passwordInput.type === "password";
        passwordInput.type = isPassword ? "text" : "password";

        // Update SVG paths exactly like your original code
        if (eyeIcon) {
            if (isPassword) {
            eyeIcon.innerHTML =
                '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
            } else {
            eyeIcon.innerHTML =
                '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
            }
        }
        });
    }

    // ---------- Form Validation ----------
    if (form && emailInput && passwordInput) {
        form.addEventListener("submit", (e) => {
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!email) {
            e.preventDefault();
            if (typeof showToast === "function") showToast("Email is required", "error");
            return;
        }

        if (!emailRegex.test(email)) {
            e.preventDefault();
            if (typeof showToast === "function") showToast("Please enter a valid email address", "error");
            return;
        }

        if (!password) {
            e.preventDefault();
            if (typeof showToast === "function") showToast("Password is required", "error");
            return;
        }
        });
    }

    // ---------- Django error toast (from json_script) ----------
    const errScript = document.getElementById("login-error");
    if (errScript) {
    let errorMsg = "";

    try {
        // json_script outputs JSON, so parse it (safe + correct)
        errorMsg = JSON.parse(errScript.textContent || '""');
    } catch (e) {
        errorMsg = (errScript.textContent || "").trim();
    }

    if (typeof errorMsg === "string") errorMsg = errorMsg.trim();

    if (errorMsg) {
        if (typeof showToast === "function") showToast(errorMsg, "error");
    }
    }

});
