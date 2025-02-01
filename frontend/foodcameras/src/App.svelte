<script>
  import { onMount } from 'svelte';
  import L from 'leaflet';
  import "leaflet/dist/leaflet.css";
  import ActivityBar from './lib/ActivityBar.svelte'; // Import the new component

  let map;
  let businessPoints = [];
  let currentImage = ""; // Stores the URL of the currently displayed image
  let currentIndex = 0; // Track the current location index
  let locations = []; // Store locations with their details for easy flipping
  let currentPin = null; // Reference to the temporary pin

  // Color mapping based on busyness level
  const getColorForLevel = (level) => {
    if (level === "Empty") return "green";
    if (level === "Low") return "yellowgreen";
    if (level === "Medium") return "orange";
    if (level === "High") return "red";
    return "gray"; // Default
  };

  // Fetch location and busyness data
  const fetchBusinessData = async () => {
    const locationsResponse = await fetch('http://localhost:5000/api/locations');
    const locationsData = await locationsResponse.json();

    for (const location of locationsData) {
      const busynessResponse = await fetch(`http://localhost:5000/api/location/${location.location_name}`);
      const busynessData = await busynessResponse.json();

      const locationData = {
        ...location,
        busyness: busynessData.map(data => ({
          camera_id: data.camera_id,
          people: data.people,
          level: data.level,
          image: data.image
        }))
      };

      businessPoints.push(locationData);
      locations.push(locationData);

      // Preload images
      busynessData.forEach(data => {
        const img = new Image();
        img.src = `http://localhost:5000/api/image/${data.image}`;
      });
    }
  };

  // Update the current image when a marker is clicked
  const updateCurrentImage = (image) => {
    currentImage = `http://localhost:5000/api/image/${image}`;
  };

  // Handle sidebar location selection
  const selectLocation = (index) => {
    currentIndex = index;
    const selectedLocation = locations[index];
    const imageToShow = selectedLocation.busyness[0]?.image || ""; // Show first camera image by default

    // Update current image and sidebar details
    if (imageToShow) {
      updateCurrentImage(imageToShow);
      document.getElementById('location-name').innerText = selectedLocation.location_name;
    }

    // Center the map on the selected location's coordinates
    if (selectedLocation.latitude && selectedLocation.longitude) {
      if (currentPin) {
        map.removeLayer(currentPin); // Remove the existing pin if any
      }
      currentPin = L.marker([selectedLocation.longitude, selectedLocation.latitude]).addTo(map); // Add a new pin
      map.setView([selectedLocation.longitude, selectedLocation.latitude], 20);
    }
  };

  onMount(async () => {
    try {
      // Initialize the map
      map = L.map('map').setView([33.512950, -112.127405], 17);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

      // Fetch data and add markers
      await fetchBusinessData();
      businessPoints.forEach((location, index) => {
        const { latitude, longitude, location_name, busyness } = location;

        if (latitude && longitude) {
          const totalPeople = busyness.reduce((sum, b) => sum + b.people, 0);
          const color = getColorForLevel(busyness[0].level);

          // Add marker with click event
          const marker = L.marker([longitude, latitude])
            .addTo(map)
            .bindPopup(`
              <b>${location_name}</b><br>
              People: ${totalPeople}<br>
              Traffic: ${busyness[0].level}
            `);

          // Add an icon with a colored circle for busyness
          const icon = L.divIcon({
            className: "custom-icon",
            html: `
              <div style="
                background-color: ${color};
                border-radius: 50%;
                width: 12px;
                height: 12px;
                display: inline-block;
                margin-right: 5px;
              "></div>
            `
          });

          marker.setIcon(icon);

          // Set click handler to update the image and sidebar
          marker.on('click', () => {
            const imageToShow = busyness[0]?.image || ""; // Use the first camera's image if available
            if (imageToShow) {
              updateCurrentImage(imageToShow);
              document.getElementById('location-name').innerText = location_name;
            }
          });
        }
      });
    } catch (error) {
      console.error("Error loading map data:", error);
    }
  });
</script>

<!-- Sidebar for location details and image navigation -->
<div class="sidebar">
  <h3 id="location-name">{locations[currentIndex]?.location_name || "Location"}</h3>
  <h5 id="location-name">{locations[currentIndex]?.busyness[0].level || "Location"}</h5>
  {#if currentImage}
    <img class="sidebar-image" src={currentImage} alt="Location Image" />
  {/if}
  <ActivityBar locationName={locations[currentIndex]?.location_name} />
  <div class="buttons">
    <button on:click={() => selectLocation((currentIndex - 1 + locations.length) % locations.length)}>Previous</button>
    <button on:click={() => selectLocation((currentIndex + 1) % locations.length)}>Next</button>
  </div>
</div>

<div id="map" style="height: 100%;"></div>

<style>
  #map {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    z-index: 0;
  }

  .sidebar {
    position: fixed; /* Ensures the sidebar stays fixed on the left */
    top: 0;
    left: 0;
    width: 300px; /* Increased width for more space */
    height: 100vh; /* Full height of the viewport */
    background: #fff;
    border-right: 1px solid #ccc; /* Adjust for a cleaner division */
    padding: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    z-index: 1;
    overflow-y: auto; /* Allows scrolling if content exceeds the height */
    font-family: 'Arial', sans-serif; /* Changed to sans-serif */
  }

  .sidebar-image {
    width: 100%; /* Make the image fit the sidebar's width */
    height: auto; /* Maintain aspect ratio */
    max-height: 200px; /* Set a reasonable maximum height */
    object-fit: cover; /* Ensures the image fits within bounds */
    border-radius: 8px;
  }

  .custom-icon {
    display: flex;
    align-items: center;
    font-size: 12px;
    font-weight: bold;
  }

  .activity-bar {
    height: 150px; /* Adjust as needed for a reasonable display of activity data */
    width: 100%;
    background: #eee;
    border-radius: 8px;
    margin-top: 10px;
  }

  .buttons {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
  }

  .buttons button {
    padding: 5px 10px;
    background: #007bff;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }

  .buttons button:hover {
    background: #0056b3;
  }
</style>
