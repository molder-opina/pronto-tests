# Analytics API Tests

Comprehensive test suite for all analytics/reports endpoints.

## Test Structure

```
tests/functionality/api/analytics/
├── conftest.py                        # Pytest fixtures and configuration
├── test_revenue_reports.py            # Revenue analytics tests
├── test_employee_reports.py           # Employee analytics tests
├── test_product_customer_reports.py   # Product & customer analytics tests
└── test_operational_reports.py        # Operational metrics tests
```

## Test Coverage

### Revenue Reports
- `/api/reports/kpis` - Key performance indicators
- `/api/reports/sales` - Sales trends with granularity
- `/api/reports/peak-hours` - Peak hours analysis

### Employee Reports
- `/api/reports/waiter-performance` - Waiter performance metrics
- `/api/reports/waiter-tips` - Waiter tips analysis

### Product & Customer Reports
- `/api/reports/top-products` - Top selling products
- `/api/reports/category-performance` - Category performance
- `/api/reports/customer-segments` - Customer segmentation

### Operational Reports
- `/api/reports/operational-metrics` - Operational metrics (prep/delivery times)

## Running Tests

### All analytics tests
```bash
pytest tests/functionality/api/analytics/ -v
```

### Specific test file
```bash
pytest tests/functionality/api/analytics/test_revenue_reports.py -v
```

### Specific test class
```bash
pytest tests/functionality/api/analytics/test_revenue_reports.py::TestRevenueReports -v
```

### Specific test
```bash
pytest tests/functionality/api/analytics/test_revenue_reports.py::TestRevenueReports::test_kpis_endpoint -v
```

### With coverage
```bash
pytest tests/functionality/api/analytics/ --cov=pronto_shared.services.analytics --cov-report=html
```

## Test Scenarios

Each test suite covers:
- ✅ Successful requests with valid data
- ✅ Response structure validation
- ✅ Data type validation
- ✅ Range validation (percentages, counts, etc.)
- ✅ Authentication requirements
- ✅ Edge cases (no data, future dates, invalid dates)
- ✅ Sorting and ordering
- ✅ Business logic validation

## Prerequisites

- API server running on `http://localhost:6082`
- Admin user credentials: `admin@pronto.test` / `admin123`
- Database with seed data

## Fixtures

### `authenticated_client`
Provides an authenticated HTTP client with admin credentials.

### `client`
Provides an unauthenticated HTTP client for testing auth requirements.

### `date_range`
Provides a standard 7-day date range for tests.

### `sample_date_range`
Provides a reusable date range fixture.

## Example Usage

```python
def test_my_report(authenticated_client, date_range):
    response = authenticated_client.get(
        "/api/reports/my-report",
        params=date_range
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

## Notes

- All tests use session-scoped authentication to avoid repeated logins
- Tests validate both structure and business logic
- Edge cases include future dates, invalid dates, and empty data sets
- All endpoints require authentication (401 without auth)
