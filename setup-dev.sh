#!/bin/bash

# Real-Time AI Voice Agent - Development Setup Script
# This script sets up the complete development environment

set -e

echo "🎤 Setting up Real-Time AI Voice Agent Development Environment"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_header "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3.8+ is required but not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 18+ is required but not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Container deployment will not be available"
    fi
    
    print_status "System requirements check completed"
}

# Setup backend
setup_backend() {
    print_header "Setting up backend environment..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate || source venv/Scripts/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating backend .env file..."
        cp .env.example .env
        print_warning "Please update .env file with your API keys!"
    fi
    
    cd ..
    print_status "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    print_header "Setting up frontend environment..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Create .env.local file if it doesn't exist
    if [ ! -f ".env.local" ]; then
        print_status "Creating frontend .env.local file..."
        cp .env.example .env.local
    fi
    
    cd ..
    print_status "Frontend setup completed"
}

# Create development scripts
create_dev_scripts() {
    print_header "Creating development scripts..."
    
    # Backend development script
    cat > dev-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting backend development server..."
cd backend
source venv/bin/activate || source venv/Scripts/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF
    
    # Frontend development script
    cat > dev-frontend.sh << 'EOF'
#!/bin/bash
echo "🎨 Starting frontend development server..."
cd frontend
npm run dev
EOF
    
    # Full development script
    cat > dev-full.sh << 'EOF'
#!/bin/bash
echo "🎤 Starting full development environment..."
echo "Backend will run on http://localhost:8000"
echo "Frontend will run on http://localhost:3000"
echo "Press Ctrl+C to stop all servers"

# Start backend in background
cd backend
source venv/bin/activate || source venv/Scripts/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend in background
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF
    
    # Make scripts executable
    chmod +x dev-backend.sh dev-frontend.sh dev-full.sh
    
    print_status "Development scripts created"
}

# Main setup function
main() {
    print_header "Real-Time AI Voice Agent Setup"
    
    check_requirements
    setup_backend
    setup_frontend
    create_dev_scripts
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update backend/.env with your Google API key"
    echo "2. Update frontend/.env.local if needed"
    echo "3. Run './dev-full.sh' to start both servers"
    echo ""
    echo "Development URLs:"
    echo "- Backend API: http://localhost:8000"
    echo "- Frontend: http://localhost:3000"
    echo "- API Docs: http://localhost:8000/docs"
    echo ""
    echo "Performance targets:"
    echo "- Voice-to-Voice Latency: <500ms"
    echo "- Connection Setup: <2 seconds"
    echo "- Form Operations: <1 second"
}

# Run main function
main "$@"
