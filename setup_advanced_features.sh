#!/bin/bash

# Elite Wealth Capital - Advanced Features Setup Script
# This script installs dependencies and sets up the new features

set -e  # Exit on error

echo "=========================================="
echo "Elite Wealth Capital - Advanced Features"
echo "Setup Script"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found."
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "⚠️  Could not find virtual environment activation script"
fi

# Install dependencies
echo ""
echo "Installing Python dependencies..."
echo "This may take a few minutes..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found."
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "📝 IMPORTANT: Edit .env file with your credentials:"
    echo "   - SECRET_KEY"
    echo "   - Database settings"
    echo "   - Payment gateway credentials (Stripe, PayPal, Coinbase)"
    echo "   - Email settings"
fi

# Create migrations
echo ""
echo "Creating database migrations..."
python manage.py makemigrations messaging

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Configure payment gateways:"
echo "   - Stripe: https://dashboard.stripe.com/apikeys"
echo "   - PayPal: https://developer.paypal.com/dashboard/"
echo "   - Coinbase Commerce: https://commerce.coinbase.com/dashboard/settings"
echo ""
echo "3. Start development server:"
echo "   For HTTP only:"
echo "   $ python manage.py runserver"
echo ""
echo "   For WebSocket support:"
echo "   $ daphne -b 0.0.0.0 -p 8000 elite_wealth.asgi:application"
echo ""
echo "4. Access the API documentation:"
echo "   Swagger UI: http://localhost:8000/api/v1/swagger/"
echo "   ReDoc: http://localhost:8000/api/v1/redoc/"
echo ""
echo "5. Test API with JWT authentication:"
echo "   POST /api/v1/auth/token/ (get access token)"
echo "   Use: Authorization: Bearer <token>"
echo ""
echo "📖 See ADVANCED_FEATURES.md for detailed documentation"
echo "=========================================="
