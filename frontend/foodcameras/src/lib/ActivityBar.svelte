<script>
  import { onMount, afterUpdate } from 'svelte';
  import { Chart } from 'chart.js/auto';

  export let locationName = "";
  let canvasEl;
  let chartInstance;
  let lastLocationName = "";

  // Fetch analytics data from the new endpoint and update the chart.
  const fetchAnalyticsData = async () => {
    if (!locationName || locationName === lastLocationName) return;
    lastLocationName = locationName;

    try {
      const weekday = new Date().toLocaleString('en-US', { weekday: 'long' });
      const response = await fetch(`http://localhost:5000/api/analytics/${locationName}/${weekday}`);
      const data = await response.json();
      const filteredData = data.filter(d => d.frameStart >= "07:00" && d.frameStart <= "22:00");

      const generateTimeSlots = () => {
        const slots = [];
        let hour = 7, minute = 0;
        while (hour < 22 || (hour === 22 && minute === 0)) {
          slots.push(`${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`);
          minute += 30;
          if (minute === 60) {
            minute = 0;
            hour++;
          }
        }
        return slots;
      };
      const slots = generateTimeSlots();

      const averages = slots.map(slot => {
        const record = filteredData.find(d => d.frameStart === slot);
        return record ? record.average : 0;
      });

      updateChart(slots, averages);
    } catch (error) {
      console.error("Error fetching analytics data:", error);
    }
  };

  const updateChart = (labels, data) => {
    if (!chartInstance) return;
    chartInstance.data.labels = labels;
    chartInstance.data.datasets[0].data = data;
    chartInstance.update();
  };

  onMount(() => {
    const ctx = canvasEl.getContext('2d');
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Average People Count',
          data: [],
          backgroundColor: '#522398',
          borderColor: '#FFFFFF',
          borderWidth: 1,
          barPercentage: 1.0,
          categoryPercentage: 1.0
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true }
        },
        scales: {
          x: { 
            title: { display: true, text: 'Time' },
            ticks: { color: '#522398', font: { weight: 'bold' } },
            grid: { color: '#ccc' }
          },
          y: { 
            title: { display: true, text: 'Average People Count' },
            ticks: { color: '#522398', font: { weight: 'bold' } },
            grid: { color: '#ccc' }
          }
        }
      }
    });
    fetchAnalyticsData();
  });

  afterUpdate(() => {
    fetchAnalyticsData();
  });
</script>

<div class="activity-bar">
  <canvas bind:this={canvasEl}></canvas>
</div>

<style>
  .activity-bar {
    height: 150px;
    background: #fff;
    border: 2px solid #522398;
    border-radius: 8px;
    margin-top: 15px;
    padding: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
  }
</style>
