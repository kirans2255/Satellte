const API_BASE_URL = "http://127.0.0.1:5000";  

// 🔹 Signup Function
async function signup() {
    const username = document.getElementById("signupUsername").value;
    const password = document.getElementById("signupPassword").value;

    if (!username || !password) {
        alert("Please enter both username and password.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/signup-page`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
            alert("Signup successful! Please log in.");
            window.location.href = "/login"; // Redirect to login page
        } else {
            alert(data.error || "Signup failed.");
        }
    } catch (error) {
        console.error("Signup error:", error);
        alert("Error during signup.");
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
let map = L.map('map').setView([20, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

async function searchSatellite() {
    const satelliteId = document.getElementById("satelliteInput").value;
    if (!satelliteId) {
        alert("Please enter a NORAD ID.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/satellite/search?id=${satelliteId}`);   // ✅ Fixed template literal syntax
        const data = await response.json();

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
