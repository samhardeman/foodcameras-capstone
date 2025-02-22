<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Important Hours</title>
    <style>
        :root {
            --primary-color: #f1c40f; /* Main color */
            --secondary-color: #3498db; /* Secondary color */
            --background-color: #f9f9f9; /* Background color */
            --shadow-color: #ccc; /* Shadow color */
            --font-family: 'Open Sans', sans-serif;
        }

        body {
            font-family: var(--font-family);
            margin: 0;
            padding: 0;
            background-color: var(--background-color);
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
            padding-left: 20px;
            padding-right: 20px;
        }

        h1, h2 {
            font-weight: bold;
        }

        section {
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding-bottom: 20px;
            margin-bottom: 20px;
            width: calc(100% - 40px);
        }

        .gradient-background {
            background-image: linear-gradient(to bottom, #fff 50%, var(--primary-color) 50%);
        }
    </style>
</head>

<body>
    <h1>Important Hours</h1>
    
    <section>
        <h2>ACE Centers:</h2>
        <p>10 a.m.-8 p.m. Sunday through Thursday.</p>
    </section>
    
    <section>
        <h2>Campus Recreation Facilities:</h2>
        <ul class="list-style">
            <li><strong>Canyon Activity Center:</strong> 8 a.m.-11:30 p.m. Monday-Friday, 8 a.m.-9 p.p. Saturday and noon-9 p.m. Sunday.</li>
            <li><strong>Lopes Performance Center:</strong> 6 a.m.-11:30 p.m. Monday-Friday, 8 a.m.-9:30 p.m. Saturday and noon-9:30 p.m. Sunday.</li>
            <li><strong>Fitness Centers (Antelope, Juniper, Papago, Verde):</strong> 6 a.m.-11:30 p.m. Monday-Friday, 8 a.m.-9:30 p.p. Saturday and noon-9:30 p.m. Sunday.</li>
        </ul>
    </section>
    
    <section class="gradient-background">
        <h2>GCU Dining: Spring 2025</h2>
        <!-- Add hours or information for GCU Dining here -->
    </section>
    
    <section>
        <h2>Health Center:</h2>
        <p>7:45 a.m.-5:30 p.m. Monday to Friday.</p>
    </section>
    
    <section class="gradient-background">
        <h2>IT Help Desk:</h2>
        <ul class="list-style">
            <li><strong>Weekdays:</strong> 6 a.m.-7 p.m.</li>
            <li><strong>Saturdays:</strong> 7 a.m.-2 p.m.</li>
            <li><strong>Sunday:</strong> Closed</li>
        </ul>
    </section>
    
    <section>
        <h2>Library:</h2>
        <p>Ask-A-Librarian and campus library building hours available <a href="#">here</a>.</p>
    </section>
    
    <section class="gradient-background">
        <h2>Lope Shop:</h2>
        <ul class="list-style">
            <li><strong>Monday-Friday:</strong> 9 a.m.-7 p.m.</li>
            <li><strong>Saturday:</strong> 10 a.m.-4 p.m.</li>
        </ul>
    </section>

<script>
// No Svelte code is needed for this example
</script>
</body>
</html>