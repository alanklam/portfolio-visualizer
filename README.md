# Portfolio Visualizer

A web application that helps you analyze and visualize your stock portfolio by combining transaction data from different brokers.

## Features

- Upload and parse transaction files from multiple brokers (Fidelity, Charles Schwab, E-Trade)
- Standardize transaction data across different formats
- Calculate stock holdings and cost basis
- Track portfolio performance and gains/losses
- Visualize portfolio allocation and performance
- Set and monitor portfolio target weights

## Tech Stack

- Frontend: React.js with Plotly for visualizations
- Backend: FastAPI with SQLite database
- Deployment: Packaged as a macOS application using py2app

## Setup

### Backend

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
uvicorn backend.app.main:app --reload
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The application will be available at http://localhost:3000

## Usage

1. Navigate to the Upload page
2. Select your broker from the dropdown menu
3. Drag and drop your transaction CSV file or click to select it
4. View your portfolio analysis on the main dashboard
5. Configure target weights in the Settings page

## Supported Brokers

- Fidelity
- Charles Schwab
- E-Trade

## File Format Examples

See the documentation in `instruction/instruction.md` for detailed CSV format examples from each supported broker.

## Building for Distribution

To build the macOS application:

```bash
python scripts/deploy.py py2app
```

The packaged application will be available in the `dist` directory.

## License

MIT 