# Smart Traffic Control Dashboard

A real-time, AI-powered Smart Traffic Management System for urban congestion control. This project features a beautiful, premium glassmorphic UI built with React, Vite, and Tailwind CSS, and connects to a Flask backend for real-time vehicle detection and signal optimization.

![Smart Traffic Control Dashboard](https://lovable.dev/opengraph-image-p98pqg.png)

## Features

- **Real-Time Vehicle Counting**: Displays live data of vehicles detected at each intersection (North, South, East, West).
- **Automated Signal Optimization**: Connects to an AI-powered Flask backend to automatically cycle and optimize traffic signals based on congestion.
- **Manual Override Mode**: Allows operators to manually take control of traffic signals from the dashboard.
- **Premium Glassmorphic UI**: Features a modern cyber-dark aesthetic with dynamic radial gradients, blurred glass panels, and glowing traffic indicators.
- **Responsive Design**: Fully responsive interface tailored for both desktop and mobile traffic control centers.

## Tech Stack

- **Frontend Framework**: [React](https://reactjs.org/) + [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with custom glassmorphism utilities.
- **Components**: [shadcn/ui](https://ui.shadcn.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Fonts**: Outfit & Inter (Google Fonts)
- **Backend API Reference**: Flask (Python)

## Getting Started

### Prerequisites

You'll need Node.js and npm installed on your machine. We recommend using `nvm` (Node Version Manager).

### Installation

1. Clone the repository:
   ```bash
   git clone <YOUR_GIT_URL>
   cd tempo-traffic-control
   ```

2. Install the frontend dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The dashboard will be available at `http://localhost:5173/` (or the port specified in your terminal).

### Connecting to the Backend

By default, the dashboard attempts to connect to a local Flask backend at `http://127.0.0.1:5000`. 
If the backend is offline, the dashboard gracefully falls back to a simulated traffic feed so you can still preview the UI and animations.

## Project Structure

- `src/components/TrafficDashboard.tsx`: The main dashboard view containing all cards, traffic indicators, and control panels.
- `src/index.css`: Contains all the custom theming variables, animated gradients, and glassmorphism utilities.
- `tailwind.config.ts`: Tailwind configuration extending the theme to include our custom fonts and variables.

## License

This project is open-source and available under the MIT License.
