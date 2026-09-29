# Personal Expense Tracker

A responsive web application for tracking personal expenses, built with HTML, CSS, and JavaScript.

## Features

- Add expenses with validation (amount > 0, required category and date)
- View expenses in a table
- Categorize expenses (Food, Transport, Entertainment, Shopping, Education, Bills, Health, Other)
- Delete individual expenses
- Data persistence using browser localStorage
- Responsive design for mobile and desktop
- Summary cards showing total expenses and number of expenses

## How to Run

### Quick Start (Windows)
- **Start**: Double-click [start.bat](file:///d:/Project/start.bat) (or run `start.bat`). It starts the Node.js backend server and automatically opens `http://localhost:3000` in your default browser.
- **Stop**: Double-click [stop.bat](file:///d:/Project/stop.bat) (or run `stop.bat`). It safely terminates the server and frees port 3000.

### Manual Start
```bash
npm install
npm start
```
Then open `http://localhost:3000` in your browser.

## File Structure

- `start.bat` / `stop.bat` - One-click scripts to start and stop the server
- `server/server.js` - Express backend with CSV storage API
- `data/expenses.csv` - Auto-managed persistent CSV file
- `index.html` - The main HTML structure
- `style.css` - Professional styling for the application
- `script.js` - Application logic with asynchronous backend sync
- `README.md` - Documentation

## Data Persistence

Expenses are automatically saved to and loaded from `data/expenses.csv` on the local machine via the Node.js backend.

## Future Enhancements (Planned)

- Search and filter expenses
- Spending reports and visualizations (charts)
- Import/export CSV data
- Edit existing expenses

## Browser Support

This application uses modern web APIs and should work in all recent browsers:
- Chrome 60+
- Firefox 54+
- Safari 10.1+
- Edge 79+

## Credits

Built as a beginner-friendly project to practice web development with HTML, CSS, and JavaScript.