<script>
  import { onMount } from 'svelte';
  import L from 'leaflet';
  import "leaflet/dist/leaflet.css";

  let map;
  let businessPoints = [];
  let currentImage = ""; // Stores the URL of the currently displayed image

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
    const locations = await locationsResponse.json();

    for (const location of locations) {
      const busynessResponse = await fetch(`http://localhost:5000/api/location/${location.location_name}`);
      const busynessData = await busynessResponse.json();

      businessPoints.push({
        ...location,
        busyness: busynessData.map(data => ({
          camera_id: data.camera_id,
          people: data.people,
          level: data.level,
          image: data.image
        }))
      });

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

  onMount(async () => {
    try {
      // Initialize the map
      map = L.map('map').setView([33.512950, -112.127405], 17);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

      // Fetch data and add markers
      await fetchBusinessData();
      businessPoints.forEach(location => {
        const { latitude, longitude, location_name, busyness } = location;

        if (latitude && longitude) {
          const totalPeople = busyness.reduce((sum, b) => sum + b.people, 0);
          const maxBusynessLevel = busyness.reduce((max, b) => b.level === "High" ? "heavy" : max, "none");
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

          // Set click handler to update the image
          marker.on('click', () => {
            const imageToShow = busyness[0]?.image || ""; // Use the first camera's image if available
            if (imageToShow) updateCurrentImage(imageToShow);
          });
        }
      });
    } catch (error) {
      console.error("Error loading map data:", error);
    }
  });
</script>

<div id="map" style="height: 100%;"></div>

<div class="image-display">
  {#if currentImage}
    <img src={currentImage} alt="Location" />
  {/if}
</div>

<style>
  #map {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    z-index: 0;
  }

  .custom-icon {
    display: flex;
    align-items: center;
    font-size: 12px;
    font-weight: bold;
  }

  .image-display {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 200px;
    height: 150px;
    overflow: hidden;
    border: 1px solid #ccc;
    border-radius: 8px;
    background: #fff;
    display: flex;
    justify-content: center;
    align-items: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .image-display img {
    max-width: 100%;
    max-height: 100%;
    object-fit: cover;
  }
</style>
