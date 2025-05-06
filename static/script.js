const API_BASE_URL = "http://127.0.0.1:5000";

// 🔹 Signup Function
async function signup() {
    const username = document.getElementById("signupUsername").value.trim();
    const email = document.getElementById("signupEmail").value.trim();  // 🔹 Get email
    const password = document.getElementById("signupPassword").value.trim();

    if (!username || !email || !password) {
        Toastify({
            text: "Please fill all fields: username, email, and password.",
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "#f44336", // red
        }).showToast();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/signup-page`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password }),  // 🔹 Include email
        });

        const data = await response.json();

        if (response.ok) {
            Toastify({
                text: "Signup successful! Redirecting...",
                duration: 2000,
                gravity: "top",
                position: "right",
                backgroundColor: "#4CAF50", // green
            }).showToast();

            setTimeout(() => {
                window.location.href = "/login";
            }, 2000);
        } else {
            Toastify({
                text: data.error || "Signup failed.",
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "#f44336",
            }).showToast();
        }
    } catch (error) {
        console.error("Signup error:", error);
        Toastify({
            text: "Error during signup.",
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "#f44336",
        }).showToast();
    }
}


// 🔹 Login Function
async function login() {
    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;

    if (!username || !password) {
        alert("Please enter both username and password.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/login-page`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
            alert("Login successful!");
            localStorage.setItem("token", data.token); // Save JWT token
            window.location.href = "/"; // Redirect to dashboard
        } else {
            alert(data.error || "Invalid login.");
        }
    } catch (error) {
        console.error("Login error:", error);
        alert("Error during login.");
    }
}

// 🌍 Initialize the map globally
let map; // declare it globally

document.addEventListener('DOMContentLoaded', function () {
  map = L.map('map').setView([20, 0], 2); // initialize it here
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
});


async function searchSatellite() {
    const satelliteId = document.getElementById("satelliteInput").value;
    if (!satelliteId) {
        alert("Please enter a NORAD ID.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/satellite/search?id=${satelliteId}`);   // ✅ Fixed template literal syntax
        const data = await response.json();

        console.log("Token being sent:", token);

        if (response.ok) {
            document.getElementById("satelliteResult").innerHTML = `
                <strong>Satellite:</strong> ${data.name} <br>
                <strong>Latitude:</strong> ${data.latitude} <br>
                <strong>Longitude:</strong> ${data.longitude} <br>
                <strong>Altitude:</strong> ${data.altitude} km
            `;  // ✅ Used backticks for multiline template literals

            // Update map with new satellite position
            updateMap(data.latitude, data.longitude);
        } else {
            document.getElementById("satelliteResult").innerHTML = "Satellite not found.";
        }
    } catch (error) {
        console.error("Error fetching satellite data:", error);
        document.getElementById("satelliteResult").innerHTML = "Error fetching satellite data.";
    }
}

function updateMap(latitude, longitude) {
    if (typeof L === "undefined") {
        console.error("Leaflet.js is not loaded!");
        return;
    }

    // Move the map to the satellite's position
    map.setView([latitude, longitude], 5);

    // Remove existing markers (optional)
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    // Add new marker
    L.marker([latitude, longitude]).addTo(map)
        .bindPopup("Satellite Location")
        .openPopup();
}

// 🌙 Dark Mode Toggle
document.getElementById("toggleMode").addEventListener("click", function () {
    document.body.classList.toggle("light-mode");
});


// ✅ Utility function to handle API requests
async function fetchData(url, method, body = null) {
    try {
        const response = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: body ? JSON.stringify(body) : null,
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Invalid credentials");

        return data;
    } catch (error) {
        console.error(`Error in ${method} request:`, error);
        return null; // Return null to handle errors properly
    }
}

// 🔹 Login Function with SweetAlert
async function login() {
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if (!username || !password) {
        Swal.fire({
            icon: "warning",
            title: "Missing Fields",
            text: "Please enter both username and password.",
        });
        return;
    }

    const data = await fetchData(`${API_BASE_URL}/login-page`, "POST", { username, password });

    if (data) {
        Swal.fire({
            icon: "success",
            title: "Login Successful!",
            text: "Redirecting to dashboard...",
            timer: 2000,
            showConfirmButton: false,
        }).then(() => {
            localStorage.setItem("token", data.token); // Save JWT token
            window.location.href = "/"; // Redirect to dashboard
        });
    } else {
        Swal.fire({
            icon: "error",
            title: "Login Failed",
            text: "Incorrect username or password.",
        });
    }
}


document.getElementById('logoutBtn').addEventListener('click', async () => {
    const confirm = await Swal.fire({
        title: "Are you sure?",
        text: "You will be logged out.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#d33",
        confirmButtonText: "Yes, log me out!",
    });

    if (confirm.isConfirmed) {
        try {
            const response = await fetch('/logout', {
                method: 'POST',
            });

            if (response.ok) {
                localStorage.removeItem("token");

                Toastify({
                    text: "Logged out successfully!",
                    duration: 2000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#4CAF50",
                }).showToast();

                setTimeout(() => {
                    window.location.href = "/login";
                }, 2000);
            } else {
                Toastify({
                    text: "Logout failed.",
                    duration: 3000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#f44336",
                }).showToast();
            }
        } catch (err) {
            console.error("Logout error:", err);
            Toastify({
                text: "Error during logout.",
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "#f44336",
            }).showToast();
        }
    }
});
