# Week 2 Assignment

This repository contains a FastAPI application for working with a PostgreSQL database. It includes API routes for customers, employees, offices, orders, order details, payments, products, product lines, and count summaries.

## Project Structure

```text
app/
  crud/       Database query logic
  models/     SQLAlchemy models
  routers/    FastAPI route definitions
  schemas/    Pydantic schemas
  config.py   Environment configuration
  database.py Database connection setup
  main.py     FastAPI application entry point
```

Other important files:

```text
Dockerfile
docker-compose.yml
requirements.txt
seed.sql
Assignment_2.pdf
```

## Requirements

- Python 3.11
- PostgreSQL
- Docker and Docker Compose, if running with containers

## Environment Variables

Create a `.env` file in the project root with these values:

```env
POSTGRES_HOST=postgres
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
POSTGRES_PORT=5432
```

For local development without Docker, set `POSTGRES_HOST` to your local database host, such as `localhost`.

## Run With Docker

Build and start the API and PostgreSQL database:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation will be available at:

```text
http://localhost:8000/docs
```

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

## API Route Groups

The application includes these route groups:

```text
/
/customers
/employees
/offices
/orders
/orderdetails
/payments
/products
/productlines
/count
```

Most resource routes support listing records, retrieving one record, creating records, updating records, and deleting records.

## Database Seed Data

The `seed.sql` file is mounted into the PostgreSQL container by `docker-compose.yml`. When the database container is created for the first time, PostgreSQL runs this file to create and populate the database.

## Notes

- The main application entry point is `app/main.py`.
- The Docker container runs the app with Uvicorn on port `8000`.
- Use `/docs` to test the API endpoints from the browser.
