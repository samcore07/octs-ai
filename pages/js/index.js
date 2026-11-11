/* Home page: profile preferences and task submission. */
function getNameFromEmail(email) {
    const prefix = email.split("@")[0];
    return prefix
        .replace(/[.\_-]+/g, " ")
        .replace(/\d+/g, "")
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(" ") || "User";
}

function updateProfile(email) {
    const name = getNameFromEmail(email);
    const initial = name.charAt(0).toUpperCase();

    const welcomeName = document.getElementById("welcomeName");
    const profileName = document.getElementById("profileName");
    const profileEmail = document.getElementById("profileEmail");
    const topName = document.getElementById("topName");
    const smallAvatar = document.getElementById("smallAvatar");
    const bigAvatar = document.getElementById("bigAvatar");

    if (welcomeName) welcomeName.textContent = name;
    if (profileName) profileName.textContent = name;
    if (profileEmail) profileEmail.textContent = email;
    if (topName) topName.textContent = name;
    if (smallAvatar) smallAvatar.textContent = initial;
    if (bigAvatar) bigAvatar.textContent = initial;
}

function saveProfile() {
    const input = document.getElementById("emailInput");
    const email = input ? input.value.trim() : "";

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        alert("Please enter a valid email address.");
        return;
    }

    localStorage.setItem("harness_user_email", email);
    updateProfile(email);
    alert("Profile updated successfully!");
}

function submitTask() {
    const input = document.getElementById("chatInput");
    const task = input ? input.value.trim() : "";

    if (!task) {
        alert("Please enter a task first.");
        return;
    }

    // Connect this function to your backend API.
    console.log("Task submitted:", task);
    alert("Task received! Connect your backend to begin execution.");
}

document.addEventListener("DOMContentLoaded", () => {
    const emailInput = document.getElementById("emailInput");
    const savedEmail = localStorage.getItem("harness_user_email") || "user@example.com";

    if (emailInput) emailInput.value = savedEmail;
    updateProfile(savedEmail);
});
