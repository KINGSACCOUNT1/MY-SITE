# Elite Wealth Capital API - Quick Reference Guide

## Base URL
```
Development: http://localhost:8000/api/v1/
Production: https://your-domain.com/api/v1/
```

## Authentication

### Obtain JWT Token
```bash
POST /api/v1/auth/token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```bash
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using Token in Requests
```bash
GET /api/v1/investments/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Endpoints

### User Profile
```bash
# Get current user
GET /api/v1/users/me/
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_active": true,
  "date_joined": "2024-01-01T00:00:00Z",
  "profile": {
    "phone_number": "+1234567890",
    "country": "US",
    "kyc_verified": true,
    "account_balance": "1500.00",
    "total_invested": "5000.00",
    "total_withdrawn": "500.00"
  }
}
```

### Investment Plans
```bash
# List all active plans
GET /api/v1/investment-plans/
Authorization: Bearer <token>

Response:
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Starter Plan",
      "description": "Low-risk starter investment",
      "min_investment": "100.00",
      "max_investment": "1000.00",
      "roi_percentage": "5.00",
      "duration_days": 30,
      "risk_level": "Low",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}

# Get specific plan
GET /api/v1/investment-plans/1/
Authorization: Bearer <token>
```

### Investments
```bash
# List user's investments
GET /api/v1/investments/
Authorization: Bearer <token>

# Create new investment
POST /api/v1/investments/
Authorization: Bearer <token>
Content-Type: application/json

{
  "investment_plan": 1,
  "amount": "500.00"
}

Response:
{
  "id": 10,
  "user": 1,
  "user_email": "user@example.com",
  "investment_plan": 1,
  "plan_name": "Starter Plan",
  "plan_details": {...},
  "amount": "500.00",
  "expected_return": "525.00",
  "total_earned": "0.00",
  "status": "active",
  "start_date": "2024-01-15",
  "maturity_date": "2024-02-14",
  "created_at": "2024-01-15T10:30:00Z",
  "days_remaining": 30,
  "progress_percentage": 0
}

# Get active investments only
GET /api/v1/investments/active/
Authorization: Bearer <token>

# Get completed investments only
GET /api/v1/investments/completed/
Authorization: Bearer <token>

# Cancel investment
POST /api/v1/investments/10/cancel/
Authorization: Bearer <token>

Response:
{
  "message": "Investment cancelled successfully."
}
```

### Deposits
```bash
# List deposits
GET /api/v1/deposits/
Authorization: Bearer <token>

# Create deposit request
POST /api/v1/deposits/
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "amount": "100.00",
  "payment_method": "crypto",
  "proof_of_payment": <file>
}

# Get pending deposits
GET /api/v1/deposits/pending/
Authorization: Bearer <token>

# Get approved deposits
GET /api/v1/deposits/approved/
Authorization: Bearer <token>
```

### Withdrawals
```bash
# List withdrawals
GET /api/v1/withdrawals/
Authorization: Bearer <token>

# Create withdrawal request
POST /api/v1/withdrawals/
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": "50.00",
  "withdrawal_method": "crypto",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}

# Get pending withdrawals
GET /api/v1/withdrawals/pending/
Authorization: Bearer <token>

# Cancel withdrawal
POST /api/v1/withdrawals/5/cancel/
Authorization: Bearer <token>

Response:
{
  "message": "Withdrawal cancelled successfully."
}
```

### Transactions
```bash
# List all transactions
GET /api/v1/transactions/
Authorization: Bearer <token>

# Get recent transactions (last 10)
GET /api/v1/transactions/recent/
Authorization: Bearer <token>

Response:
{
  "count": 10,
  "results": [
    {
      "id": 25,
      "user": 1,
      "user_email": "user@example.com",
      "transaction_type": "deposit",
      "amount": "100.00",
      "description": "Crypto deposit confirmed",
      "status": "completed",
      "reference_id": "TXN-20240115-001",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Balance & Statistics
```bash
# Get balance information
GET /api/v1/balance/
Authorization: Bearer <token>

Response:
{
  "account_balance": "1500.00",
  "total_invested": "5000.00",
  "total_earned": "250.00",
  "total_withdrawn": "500.00",
  "active_investments_count": 3,
  "pending_withdrawals_count": 1
}

# Get dashboard statistics
GET /api/v1/dashboard/stats/
Authorization: Bearer <token>

Response:
{
  "total_balance": "1500.00",
  "total_invested": "5000.00",
  "total_earned": "250.00",
  "active_investments": 3,
  "completed_investments": 5,
  "pending_deposits": 0,
  "pending_withdrawals": 1,
  "roi_percentage": "5.00"
}
```

## Pagination

All list endpoints support pagination:

```bash
GET /api/v1/investments/?page=2
GET /api/v1/transactions/?page=3

Response includes:
{
  "count": 50,
  "next": "http://api.example.com/api/v1/investments/?page=3",
  "previous": "http://api.example.com/api/v1/investments/?page=1",
  "results": [...]
}
```

## Filtering & Search

```bash
# Filter by status
GET /api/v1/investments/?status=active

# Search
GET /api/v1/transactions/?search=deposit

# Ordering
GET /api/v1/investments/?ordering=-created_at
GET /api/v1/investments/?ordering=amount
```

## Error Responses

### 400 Bad Request
```json
{
  "amount": ["This field is required."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "An unexpected error occurred."
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse:
- **Authenticated users**: 100 requests per minute
- **Unauthenticated**: 20 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642348800
```

## WebSocket Connection

### Connect to Notifications
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/notifications/');

socket.onopen = function(e) {
    console.log('Connected to notification service');
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'notification') {
        // New notification received
        console.log('New notification:', data.notification);
    } else if (data.type === 'unread_count') {
        // Unread count updated
        console.log('Unread count:', data.count);
    }
};

// Mark notification as read
socket.send(JSON.stringify({
    type: 'mark_read',
    notification_id: 'uuid-here'
}));

// Mark all as read
socket.send(JSON.stringify({
    type: 'mark_all_read'
}));

// Get unread count
socket.send(JSON.stringify({
    type: 'get_unread'
}));
```

## Testing with cURL

### Get Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### Make Authenticated Request
```bash
curl -X GET http://localhost:8000/api/v1/investments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Investment
```bash
curl -X POST http://localhost:8000/api/v1/investments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"investment_plan":1,"amount":"500.00"}'
```

## Testing with Python

```python
import requests

# Base URL
BASE_URL = 'http://localhost:8000/api/v1'

# Get token
response = requests.post(f'{BASE_URL}/auth/token/', json={
    'email': 'user@example.com',
    'password': 'password123'
})
token = response.json()['access']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(f'{BASE_URL}/investments/', headers=headers)
investments = response.json()

# Create investment
response = requests.post(
    f'{BASE_URL}/investments/',
    headers=headers,
    json={'investment_plan': 1, 'amount': '500.00'}
)
new_investment = response.json()
```

## Testing with JavaScript (Fetch)

```javascript
// Get token
const response = await fetch('http://localhost:8000/api/v1/auth/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});
const {access} = await response.json();

// Make authenticated request
const investmentsResponse = await fetch('http://localhost:8000/api/v1/investments/', {
    headers: {'Authorization': `Bearer ${access}`}
});
const investments = await investmentsResponse.json();

// Create investment
const createResponse = await fetch('http://localhost:8000/api/v1/investments/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        investment_plan: 1,
        amount: '500.00'
    })
});
const newInvestment = await createResponse.json();
```

## API Documentation UI

### Swagger UI
Interactive API documentation with "Try it out" feature:
```
http://localhost:8000/api/v1/swagger/
```

### ReDoc
Clean, readable API documentation:
```
http://localhost:8000/api/v1/redoc/
```

### OpenAPI Schema
Raw OpenAPI (Swagger) specification:
```
http://localhost:8000/api/v1/schema/
```

## Support

For issues or questions:
- Email: support@elitewealthcapita.uk
- Documentation: See ADVANCED_FEATURES.md
- API Issues: Check Swagger UI for detailed endpoint documentation
