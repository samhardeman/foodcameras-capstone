<script>
  import { onMount } from 'svelte';
  import L from 'leaflet';
  import "leaflet/dist/leaflet.css";
  import ActivityBar from './lib/ActivityBar.svelte';

  let map;
  let locations = []; // Minimal list loaded from /api/locations
  let currentIndex = 0;
  let currentImage = "";
  let orderedHours = []; // Ordered hours for the current location
  let currentIsClosed = false; // Updated based on sidebar fetch

  // Array to store each location’s marker.
  let markers = [];

  // Reactive open status text.
  $: openStatus = currentIsClosed ? 'Closed' : 'Open';

  // Cache to store detailed data fetched from /api/location/[name]
  let locationDetailsCache = {};

  // Helper: convert a "HH:MM" string (24-hour) to 12-hour format.
  function formatTime(timeStr) {
    let [hour, minute] = timeStr.split(':').map(Number);
    let ampm = hour >= 12 ? 'PM' : 'AM';
    hour = hour % 12;
    if (hour === 0) hour = 12;
    return `${hour}:${minute.toString().padStart(2, '0')} ${ampm}`;
  }

  // Helper: if open and close are "00:00", return "Closed", otherwise format them.
  function formatHours(open, close) {
    if (open === "00:00" && close === "00:00") return "Closed";
    return `${formatTime(open)} - ${formatTime(close)}`;
  }

  // Helper: determine if a location is currently open based on its hours data.
  function isOpenNow(hoursData) {
    const currentDay = new Date().toLocaleString('en-US', { weekday: 'long' });
    const todaysHours = hoursData[currentDay];
    if (!todaysHours || (todaysHours.open === "00:00" && todaysHours.close === "00:00")) {
      return false;
    }
    let now = new Date();
    let currentMinutes = now.getHours() * 60 + now.getMinutes();
    let [openHour, openMinute] = todaysHours.open.split(':').map(Number);
    let [closeHour, closeMinute] = todaysHours.close.split(':').map(Number);
    let openMinutes = openHour * 60 + openMinute;
    let closeMinutes = closeHour * 60 + closeMinute;
    return currentMinutes >= openMinutes && currentMinutes < closeMinutes;
  }

  // Returns HTML for a marker icon.
  // If 'selected' is true, we return a diamond (square rotated 45°)
  // Otherwise, we return a circle.
  // Colors: if closed is true, marker is gray; otherwise:
  // - "Empty" or "Low" → green, "Medium" → yellow, "High" → red.
  const getIconHtml = (level, closed = false, selected = false) => {
    let bg;
    if (closed) {
      bg = "#9E9E9E";
    } else {
      if (level === "Empty" || level === "Low") {
        bg = "#00C851";
      } else if (level === "Medium") {
        bg = "#FFEB3B";
      } else if (level === "High") {
        bg = "#ff4444";
      } else {
        bg = "#9E9E9E";
      }
    }
    // If selected, use a diamond shape (rotated square), else a circle.
    const borderRadius = selected ? "0" : "50%";
    const transform = selected ? "rotate(45deg)" : "";
    return `<div style="
      background-color: ${bg};
      border: 2px solid #000;
      border-radius: ${borderRadius};
      width: 16px;
      height: 16px;
      transform: ${transform};
      box-shadow: 0 0 8px rgba(0,0,0,0.6);
    "></div>`;
  };

  // Pre-fetch hours for all locations so we can mark them as open or closed.
  const prefetchAllHours = async () => {
    await Promise.all(locations.map(async loc => {
      try {
        const res = await fetch(`http://localhost:5000/api/hours/${loc.name}`);
        const hoursData = await res.json();
        loc.hoursData = hoursData; // store full hours data in the location object
        loc.isOpen = isOpenNow(hoursData);
      } catch (error) {
        console.error("Error fetching hours for", loc.name, error);
        loc.isOpen = false;
      }
    }));
  };

  // Fetch the minimal list of locations.
  const fetchLocations = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/locations');
      locations = await response.json();
      if (locations.length) {
        await prefetchAllHours(); // Determine open status for each location
        // Select the first location on load.
        await selectLocation(0);
      }
    } catch (error) {
      console.error("Error fetching locations:", error);
    }
  };

  // Fetch detailed data (including image) for a given location.
  const fetchLocationDetails = async (name) => {
    try {
      const response = await fetch(`http://localhost:5000/api/location/${name}`);
      return await response.json();
    } catch (error) {
      console.error(`Error fetching details for ${name}:`, error);
      return null;
    }
  };

  // Update the current image URL.
  const updateCurrentImage = (image) => {
    currentImage = `http://localhost:5000/api/image/${image}`;
  };

  // Fetch hours data for the selected location (for the sidebar).
  const fetchHoursDataForSidebar = async (name) => {
    try {
      const response = await fetch(`http://localhost:5000/api/hours/${name}`);
      const data = await response.json();
      // Order the week starting with today.
      const weekDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
      const currentDay = new Date().toLocaleString('en-US', { weekday: 'long' });
      let idx = weekDays.indexOf(currentDay);
      if (idx === -1) idx = 0;
      const orderedDays = weekDays.slice(idx).concat(weekDays.slice(0, idx));
      orderedHours = orderedDays.map(day => ({ day, open: data[day]?.open, close: data[day]?.close }));
      // Update currentIsClosed based on today's hours.
      const todaysHours = data[currentDay];
      if (!todaysHours || (todaysHours.open === "00:00" && todaysHours.close === "00:00")) {
        currentIsClosed = true;
      } else {
        currentIsClosed = !isOpenNow(data);
      }
    } catch (error) {
      console.error("Error fetching hours data for sidebar:", error);
    }
  };

  // Update the icons for all markers based on the current selection.
  function updateMarkersIcons() {
    locations.forEach((loc, i) => {
      const marker = markers[i];
      // For each marker, use diamond shape if it is selected.
      marker.setIcon(L.divIcon({
        className: 'custom-icon',
        html: getIconHtml(loc.trafficLevel, !loc.isOpen, i === currentIndex)
      }));
    });
  }

  // When a location is selected, update the sidebar and marker icons.
  const selectLocation = async (index) => {
    currentIndex = index;
    const loc = locations[index];

    // Center the map on the selected location.
    if (loc.latitude && loc.longitude) {
      map.setView([loc.latitude, loc.longitude], 20);
    }

    // Fetch detailed data if not already cached.
    if (!locationDetailsCache[loc.name]) {
      locationDetailsCache[loc.name] = await fetchLocationDetails(loc.name);
    }
    const details = locationDetailsCache[loc.name];
    if (details && details[0].image) {
      updateCurrentImage(details[0].image);
    }
    // Update sidebar title.
    document.getElementById('location-name').innerText = loc.name;
    // Refresh sidebar hours and open status.
    await fetchHoursDataForSidebar(loc.name);
    document.getElementById('traffic-level').innerHTML =
      `${loc.trafficLevel || ""} - <span style="color: ${currentIsClosed ? 'red' : 'green'};">${openStatus}</span>`;
    
    // Update markers so that the selected one becomes a diamond.
    updateMarkersIcons();

    // Preload previous and next location details.
    const prevIndex = (index - 1 + locations.length) % locations.length;
    const nextIndex = (index + 1) % locations.length;
    const prevLoc = locations[prevIndex];
    const nextLoc = locations[nextIndex];

    if (prevLoc && !locationDetailsCache[prevLoc.name]) {
      fetchLocationDetails(prevLoc.name).then(data => {
        locationDetailsCache[prevLoc.name] = data;
      });
    }
    if (nextLoc && !locationDetailsCache[nextLoc.name]) {
      fetchLocationDetails(nextLoc.name).then(data => {
        locationDetailsCache[nextLoc.name] = data;
      });
    }
  };

  onMount(async () => {
    // Initialize the Leaflet map.
    map = L.map('map').setView([33.512950, -112.127405], 17);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    // Load minimal location data.
    await fetchLocations();

    // Add markers for each location using the pre-fetched open status.
    locations.forEach((loc, index) => {
      if (loc.latitude && loc.longitude) {
        const marker = L.marker([loc.latitude, loc.longitude], {
          icon: L.divIcon({
            className: 'custom-icon',
            html: getIconHtml(loc.trafficLevel, !loc.isOpen, index === currentIndex)
          })
        }).addTo(map);
        // Remove the popup.
        marker.off('popupopen');
        // On click, select this location.
        marker.on('click', () => selectLocation(index));
        markers.push(marker);
      }
    });
  });
</script>

<!-- Sidebar -->
<div class="sidebar">
  <h3 id="location-name">{locations[currentIndex]?.name || "Location"}</h3>
  <h5 id="traffic-level">
    {locations[currentIndex]?.trafficLevel || ""} - <span style="color: {currentIsClosed ? 'red' : 'green'};">{openStatus}</span>
  </h5>
  {#if currentImage}
    <img class="sidebar-image" src={currentImage} alt="Location Image" />
  {/if}

  <!-- Hours column above the ActivityBar -->
  <div class="hours-column">
    {#each orderedHours as hr}
      <div class="day">
        <div class="day-name">{hr.day}</div>
        <div class="time">{formatHours(hr.open, hr.close)}</div>
      </div>
    {/each}
  </div>

  <ActivityBar locationName={locations[currentIndex]?.name} />
  <div class="buttons">
    <button on:click={() => selectLocation((currentIndex - 1 + locations.length) % locations.length)}>
      Previous
    </button>
    <button on:click={() => selectLocation((currentIndex + 1) % locations.length)}>
      Next
    </button>
  </div>
</div>

<!-- Map Container -->
<div id="map" style="height: 100%;"></div>

<style>
  /* Map container styling */
  #map {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    z-index: 0;
  }
  /* Sidebar styling */
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 320px;
    height: 100vh;
    background: #fff;
    border-right: 3px solid #522398;
    padding: 20px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    z-index: 1;
    overflow-y: auto;
    font-family: 'Arial', sans-serif;
  }
  .sidebar h3, .sidebar h5 {
    margin: 0;
    padding-bottom: 10px;
    color: #522398;
  }
  .sidebar-image {
    width: 100%;
    height: auto;
    max-height: 200px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 15px;
    border: 2px solid #522398;
  }
  /* Hours column styling */
  .hours-column {
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
  }
  .hours-column .day {
    margin-bottom: 5px;
    text-align: left;
    font-size: 12px;
    color: #522398;
  }
  .hours-column .day .day-name {
    font-weight: bold;
  }
  .hours-column .day .time {
    font-size: 10px;
  }
  /* Buttons styling */
  .buttons {
    display: flex;
    justify-content: space-between;
    margin-top: 15px;
  }
  .buttons button {
    flex: 1;
    margin: 0 5px;
    padding: 10px;
    background: #522398;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
  }
  .buttons button:hover {
    background: #3e187b;
  }
  .custom-icon {
    display: flex;
    align-items: center;
  }
</style>
