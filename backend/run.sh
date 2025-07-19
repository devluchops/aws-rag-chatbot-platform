#!/bin/bash

# Script para desarrollo local y testing del backend

echo "=== AWS RAG Chatbot Backend Setup ==="

# Función para instalar dependencias
install_deps() {
    echo "Installing dependencies..."
    pip install -r requirements.txt
}

# Función para ejecutar en desarrollo local
run_local() {
    echo "Starting local development server..."
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# Función para ejecutar tests
run_tests() {
    echo "Running tests..."
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    if [ -d "tests" ]; then
        python -m pytest tests/ -v
    else
        echo "No tests directory found"
    fi
}

# Función para crear .env desde .env.example
setup_env() {
    if [ ! -f .env ]; then
        echo "Creating .env file from .env.example..."
        cp .env.example .env
        echo "Please edit .env with your actual values"
    else
        echo ".env file already exists"
    fi
}

# Función para build con SAM
build_sam() {
    echo "Building with SAM..."
    cd ..
    sam build
    cd backend
}

# Función para testing con SAM local
test_sam() {
    echo "Testing with SAM local..."
    cd ..
    sam local start-api --host 0.0.0.0 --port 3000 --parameter-overrides "OpenSearchEndpoint=https://your-domain.us-east-1.es.amazonaws.com OpenSearchPassword=your-password"
    cd backend
}

# Función para invocar función específica
invoke_function() {
    local function_name=${1:-ChatbotFunction}
    echo "Invoking function: $function_name"
    cd ..
    sam local invoke $function_name
    cd backend
}

# Función para deploy
deploy_sam() {
    echo "Deploying with SAM..."
    cd ..
    sam deploy --guided
    cd backend
}

# Función principal
case "$1" in
    install)
        install_deps
        ;;
    setup)
        setup_env
        ;;
    dev)
        run_local
        ;;
    test)
        run_tests
        ;;
    build)
        build_sam
        ;;
    sam)
        test_sam
        ;;
    invoke)
        invoke_function $2
        ;;
    deploy)
        deploy_sam
        ;;
    *)
        echo "Usage: $0 {install|setup|dev|test|build|sam|invoke|deploy}"
        echo "  install - Install dependencies"
        echo "  setup   - Setup .env file"
        echo "  dev     - Run local development server"
        echo "  test    - Run tests"
        echo "  build   - Build with SAM"
        echo "  sam     - Test with SAM local"
        echo "  invoke  - Invoke specific function (invoke ChatbotFunction)"
        echo "  deploy  - Deploy with SAM"
        exit 1
esac
