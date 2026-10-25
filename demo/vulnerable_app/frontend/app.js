// Frontend bundle for demo vulnerable application
// Demonstrates sensitive token exposure in client-side scripts

// FAKE-DEMO-KEY: Public stripe test token
const STRIPE_PUBLISHABLE_KEY = "pk_test_51MockClientTokenPlantedForScanningVerification001122";  // FAKE-DEMO-KEY

// FAKE-DEMO-KEY: Erroneously bundled backend API secret in frontend code
const BUNDLED_INTERNAL_SECRET = "sec_demo_internal_token_998877665544332211";  // FAKE-DEMO-KEY

function fetchUser() {
    fetch('/user?id=1')
        .then(response => response.json())
        .then(data => console.log('User loaded:', data));
}

document.addEventListener('DOMContentLoaded', fetchUser);
