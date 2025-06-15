#!/bin/bash

# GitAIOps Platform Run Script

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}GitAIOps Platform Startup Script${NC}"
echo "================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: Conda not found. Please install Miniconda first.${NC}"
    exit 1
fi

# Initialize conda for bash
source $(conda info --base)/etc/profile.d/conda.sh

# Check if conda environment exists
if ! conda env list | grep -q "^gitaiops "; then
    echo -e "${YELLOW}Creating conda environment 'gitaiops'...${NC}"
    conda create -n gitaiops python=3.11 -y
    echo -e "${GREEN}Conda environment created.${NC}"
fi

# Activate conda environment
echo -e "${YELLOW}Activating conda environment...${NC}"
conda activate gitaiops

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}.env file created. Please update it with your configuration.${NC}"
fi

# Export Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the application
echo -e "${GREEN}Starting GitAIOps Platform...${NC}"
echo "API will be available at http://localhost:8080"
echo "API docs will be available at http://localhost:8080/docs"
echo "Press Ctrl+C to stop"
echo ""

python src/main.py
