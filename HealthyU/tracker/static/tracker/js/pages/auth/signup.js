document.addEventListener("DOMContentLoaded", () => {
  // -------- Password toggle (SVG path swap) --------
  const toggleBtn = document.getElementById("togglePasswordBtn");
  const passwordInput = document.getElementById("passwordInput");
  const eyeIcon = document.getElementById("eyeIcon"); // the SVG element that holds paths

  if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener("click", () => {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";

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

  // -------- Signup form validation --------
  const form = document.getElementById("signupForm");
  if (form) {
    form.addEventListener("submit", (e) => {
      const firstName = (document.getElementById("firstNameInput")?.value || "").trim();
      const lastName = (document.getElementById("lastNameInput")?.value || "").trim();
      const email = (document.getElementById("emailInput")?.value || "").trim();
      const dob = document.getElementById("dobInput")?.value || "";
      const password = document.getElementById("passwordInput")?.value || "";

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const nameRegex = /^[A-Za-z\s]+$/;
      const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{6,}$/;

      const toast = (msg) => { if (typeof showToast === "function") showToast(msg, "error"); };

      if (!firstName) { e.preventDefault(); toast("First name is required"); return; }
      if (!nameRegex.test(firstName)) { e.preventDefault(); toast("First name should only contain letters and spaces"); return; }

      if (!lastName) { e.preventDefault(); toast("Last name is required"); return; }
      if (!nameRegex.test(lastName)) { e.preventDefault(); toast("Last name should only contain letters and spaces"); return; }

      if (!email) { e.preventDefault(); toast("Email is required"); return; }
      if (!emailRegex.test(email)) { e.preventDefault(); toast("Please enter a valid email address"); return; }

      if (!dob) { e.preventDefault(); toast("Date of birth is required"); return; }

      const selectedDate = new Date(dob);
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (selectedDate >= today) { e.preventDefault(); toast("Date of birth cannot be today or in the future"); return; }

      const minDate = new Date();
      minDate.setFullYear(minDate.getFullYear() - 120);
      if (selectedDate < minDate) { e.preventDefault(); toast("Please enter a valid date of birth"); return; }

      if (!password) { e.preventDefault(); toast("Password is required"); return; }
      if (!passwordRegex.test(password)) {
        e.preventDefault();
        toast("Password must be at least 6 characters with uppercase, lowercase, number and special character");
        return;
      }
    });
  }

  // -------- Django error toast (from json_script) --------
  const errScript = document.getElementById("signup-error");
  if (errScript) {
    let errorMsg = "";
    try {
      errorMsg = JSON.parse(errScript.textContent || '""');
    } catch {
      errorMsg = (errScript.textContent || "").trim();
    }
    if (typeof errorMsg === "string") errorMsg = errorMsg.trim();
    if (errorMsg && typeof showToast === "function") showToast(errorMsg, "error");
  }
});
