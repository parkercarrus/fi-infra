## Workflow Overview

### 1. Connect to APIs
- Integrate with:
    - **Google Sheets** / **BNY** for trade data
    - **YFinance** or alternatives for stock prices
- Retrieve:
    - Trade history
    - Current position share prices

### 2. Aggregate Information to Database
- Store positions and portfolio values in database tables
- Schedule automatic refresh (e.g., every 60 minutes)

### 3. Process and Analyze Data
- Calculate portfolio metrics:
    - Total value
    - Gains/losses
- Generate statistical summaries

### 4. Visualize Results
- Build dashboards and charts for portfolio overview
- Enable CSV export for further analysis