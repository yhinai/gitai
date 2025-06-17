# GitAIOps Dashboard

Beautiful, elegant, and minimalist real-time dashboard for the GitAIOps Platform.

## Features

- **Split-screen Layout**: System status on the left, real-time activity on the right
- **Real-time Updates**: Live data every 2 seconds from the GitAIOps API
- **Elegant Design**: Glass morphism effects, smooth animations, and modern UI
- **Responsive**: Works on desktop, tablet, and mobile devices
- **TypeScript**: Fully typed for better development experience

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Architecture

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Lucide React** for icons
- **Custom hooks** for real-time data fetching

## Components

- `SystemOverview` - Left panel showing system status and configuration
- `ActivityFeed` - Right panel showing real-time activity and events
- `StatusCard` - Reusable status indicator cards
- `useRealTimeData` - Custom hook for API data fetching

## Development

The dashboard automatically connects to the GitAIOps API at `http://localhost:8000` and updates in real-time.

### Available Scripts

- `npm start` - Development server with hot reload
- `npm run build` - Production build
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended)

## Integration

The dashboard is automatically served by the FastAPI backend at `/dashboard` when built.

To rebuild and deploy:

```bash
npm run build
# Dashboard is now available at http://localhost:8000/dashboard
``` 