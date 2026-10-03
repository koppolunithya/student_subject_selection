// Fill the login form with demo credentials and submit it
function demoLogin(id, password) {
  document.getElementById("student_id").value = id;
  document.getElementById("password").value = password;
  document.getElementById("loginForm").submit();
}

// Ask for confirmation before remove/delete actions
document.querySelectorAll(".confirm-form").forEach(function (form) {
  form.addEventListener("submit", function (e) {
    if (!confirm(form.dataset.confirm || "Are you sure?")) e.preventDefault();
  });
});

// Auto-hide success/info alerts after 4 seconds
setTimeout(function () {
  document.querySelectorAll(".alert-success, .alert-info").forEach(function (el) {
    bootstrap.Alert.getOrCreateInstance(el).close();
  });
}, 4000);
