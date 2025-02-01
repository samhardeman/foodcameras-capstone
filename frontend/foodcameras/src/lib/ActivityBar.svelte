<script>
  import { onMount, afterUpdate, reactive } from 'svelte';
  import { Chart } from 'chart.js/auto';

  export let locationName = "";
  let chart;
  let analyticsData = [];
  let lastLocationName = "";

  // Fetch analytics data only when location changes
  const fetchAnalyticsData = async () => {
    if (!locationName || locationName === lastLocationName) return; // Skip if same location
    
    lastLocationName = locationName; // Store the last location name

    try {
      const response = await fetch(`http://127.0.0.1:5000/api/analytics/${locationName}`);
      const data = await response.json();

      if (!data || data.length === 0) {
        console.warn(`No analytics data found for ${locationName}`);
        analyticsData = [];
        updateChart(); // Clear chart if no data
        return;
      }

      // Convert timestamps and group data by hour
      const groupedData = {};
      
      data.forEach(d => {
        const date = new Date(d.timestamp);
        // Use only the hour and minute from the timestamp and format it as HH:00
        const hourKey = `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

        if (!groupedData[hourKey]) {
          groupedData[hourKey] = { total: 0, count: 0 };
        }

        groupedData[hourKey].total += d.people_count;
        groupedData[hourKey].count += 1;
      });

      // Compute the average for each hour
      analyticsData = Object.entries(groupedData)
        .map(([hour, { total, count }]) => ({
          timestamp: hour,
          people_count: Math.round(total / count) // Average count per hour
        }))
        .sort((a, b) => new Date(`1970/01/01 ${a.timestamp}`) - new Date(`1970/01/01 ${b.timestamp}`)); // Sort by hour

      updateChart();
    } catch (error) {
      console.error("Error fetching analytics data:", error);
    }
  };

  const updateChart = () => {
    if (!chart) return;

    if (analyticsData.length === 0) {
      chart.data.labels = [];
      chart.data.datasets[0].data = [];
    } else {
      const timestamps = analyticsData.map(d => d.timestamp);
      const peopleCounts = analyticsData.map(d => d.people_count);

      chart.data.labels = timestamps;
      chart.data.datasets[0].data = peopleCounts;
    }
    
    chart.update();
  };

  onMount(() => {
    // Initialize the chart
    const ctx = chart.getContext('2d');
    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Number of People',
          data: [],
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          barPercentage: 1.0,
          categoryPercentage: 1.0
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true },
        },
        scales: {
          x: { title: { display: true, text: 'Time' } }, // Keep timestamps
          y: { title: { display: true, text: 'Avg People Count' } },
        },
      },
    });

    fetchAnalyticsData();
  });

  afterUpdate(() => {
    // Re-fetch only if location name has changed (this avoids multiple unnecessary fetches)
    fetchAnalyticsData();
  });
</script>

<div class="activity-bar">
  <canvas bind:this={chart}></canvas>
</div>
