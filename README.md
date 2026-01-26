# Business Revenue & Performance Dashboard

A web-based dashboard for analyzing sales performance across product categories, sales channels, and geographic regions. Built with Streamlit to provide interactive filtering and real-time metric calculations.

## Problem Statement

Businesses need to quickly assess sales performance across multiple dimensions to make informed decisions. This dashboard addresses the challenge of aggregating and visualizing sales data by providing an interactive interface that allows stakeholders to filter and analyze revenue metrics without requiring technical expertise.

## Business Metrics

The dashboard displays three key performance indicators:

- **Total Revenue**: Sum of all sales revenue, filtered by selected criteria
- **Units Sold**: Total quantity of products sold
- **Average Selling Price**: Revenue per unit, calculated as total revenue divided by units sold

These metrics help identify:
- Revenue trends over time
- Performance differences across categories, channels, and regions
- Pricing effectiveness and sales volume relationships

## Data Handling

The application uses synthetic sales data generated programmatically for demonstration purposes. This approach ensures:

- **Reproducibility**: Data generation uses a fixed random seed (42), producing consistent results across runs
- **Realistic patterns**: Includes seasonal variations, promotional pricing effects, and multi-dimensional attributes (category, product, channel, region)
- **No external dependencies**: Eliminates the need for sensitive production data or complex data pipelines during development

The data includes daily sales records over a 365-day period with the following dimensions:
- Date
- Category (Beverages, Snacks, Household, Personal Care)
- Product
- Unit Price
- Units Sold
- Revenue
- Channel (Online, In-store)
- Region (North, South, East, West)

## Local Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd business-revenue-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

## Technologies

- **Streamlit**: Web framework for building the interactive dashboard interface
- **Pandas**: Data manipulation and aggregation
- **NumPy**: Numerical operations for data generation
- **Plotly**: Interactive visualization library for revenue trend charts

## Future Improvements

- **CSV Upload**: Allow users to upload their own sales data files for analysis
- **Database Integration**: Replace file-based storage with a database (PostgreSQL, SQLite) for better scalability and concurrent access
- **Deployment**: Configure for cloud deployment (Streamlit Cloud, Heroku, AWS) with proper environment handling
- **Additional Visualizations**: Add charts for category breakdown, channel comparison, and regional analysis
- **Date Range Selection**: Enable custom date range filtering beyond the current categorical filters
- **Export Functionality**: Allow users to export filtered results to CSV or PDF
