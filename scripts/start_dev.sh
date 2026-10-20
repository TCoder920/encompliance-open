#!/bin/bash

echo "🚀 Starting EnCompliance Backend Development Environment..."
echo "=================================================="

# Check if stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "❌ Error: Stripe CLI is not installed."
    echo "📥 Please install it from: https://stripe.com/docs/stripe-cli"
    echo "   Or run: brew install stripe/stripe-cli/stripe"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found."
    echo "📝 Please create it with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found."
    echo "📝 Please create .env file with required environment variables."
    echo "   See PAYMENT_SETUP.md for details."
fi

# Start Stripe webhook listener in background
echo "🔗 Starting Stripe webhook listener..."
echo "   This will forward webhooks from Stripe to localhost:8000"

# Capture webhook listener output to extract signing secret
stripe listen --forward-to localhost:8000/api/v1/payments/webhook > webhook_output.log 2>&1 &
STRIPE_PID=$!

# Wait a moment for the listener to start and output the signing secret
sleep 3

# Extract webhook secret from output
if [ -f "webhook_output.log" ]; then
    WEBHOOK_SECRET=$(grep -o "whsec_[a-zA-Z0-9]*" webhook_output.log | head -1)
    if [ ! -z "$WEBHOOK_SECRET" ]; then
        echo "🔑 Webhook signing secret detected: $WEBHOOK_SECRET"
        
        # Check if webhook secret is in .env
        if [ -f ".env" ] && grep -q "STRIPE_WEBHOOK_SECRET" .env; then
            CURRENT_SECRET=$(grep "STRIPE_WEBHOOK_SECRET" .env | cut -d'=' -f2)
            if [ "$CURRENT_SECRET" != "$WEBHOOK_SECRET" ]; then
                echo "⚠️  Webhook secret in .env doesn't match current listener!"
                echo "   Current in .env: $CURRENT_SECRET"
                echo "   Listener secret: $WEBHOOK_SECRET"
                echo "   Please update .env and restart backend server."
            else
                echo "✅ Webhook secret in .env matches listener"
            fi
        else
            echo "📝 Add this to your .env file:"
            echo "   STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET"
            echo "   Then restart the backend server."
        fi
    fi
fi

echo "✅ Stripe webhook listener started (PID: $STRIPE_PID)"
echo "   Logs: tail -f webhook_output.log"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down development environment..."
    
    # Kill stripe listener
    if kill -0 $STRIPE_PID 2>/dev/null; then
        kill $STRIPE_PID 2>/dev/null
        echo "✅ Stripe webhook listener stopped"
    fi
    
    # Clean up log file
    rm -f webhook_output.log
    
    echo "👋 Development environment stopped"
    exit 0
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Wait a moment to ensure webhook listener is ready
echo "⏳ Waiting for webhook listener to initialize..."
sleep 2

# Start the backend server
echo "🖥️  Starting backend server on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Admin: http://localhost:8000/admin"
echo ""
echo "💡 Tips:"
echo "   - Frontend should run on http://localhost:5174"
echo "   - Test payments will be processed through Stripe test mode"
echo "   - Check webhook_output.log for webhook events"
echo "   - Press Ctrl+C to stop both services"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# This line will only be reached if uvicorn exits
cleanup 