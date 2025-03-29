const API_BASE_URL = "http://127.0.0.1:5000";  

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
        const response = await fetch(`${API_BASE_URL}/satellite/search?id=${satelliteId}`);
        const data = await response.json();

        if (response.ok) {
            document.getElementById("satelliteResult").innerHTML = `
                <strong>Satellite:</strong> ${data.name} <br>
                <strong>Latitude:</strong> ${data.latitude} <br>
                <strong>Longitude:</strong> ${data.longitude} <br>
                <strong>Altitude:</strong> ${data.altitude} km
            `;

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


document.addEventListener("DOMContentLoaded", () => {
    
    // 🔥 Handle Signup Form
    const signupForm = document.getElementById("signupForm");
    if (signupForm) {
        signupForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            const response = await fetch("/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                alert("Signup successful! Please login.");
                window.location.href = "/login";
            } else {
                const data = await response.json();
                alert(data.error);
            }
        });
    }

    // 🔥 Handle Login Form
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Store token in localStorage
                localStorage.setItem("token", data.token);
                window.location.href = "/";
            } else {
                alert(data.error);
            }
        });
    }
});
