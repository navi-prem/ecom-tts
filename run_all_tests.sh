#!/bin/bash
# Master test script for E-Commerce TTS with Orchestrator

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  E-Commerce TTS - Unified Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to check if service is running
check_service() {
    local name=$1
    local url=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name is NOT running"
        return 1
    fi
}

# Step 1: Check all required services
echo -e "\n${YELLOW}Step 1: Checking Required Services...${NC}"

SERVICES_OK=true

# Check Qdrant
if ! curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Qdrant is not running on port 6333"
    echo "  Start with: just start"
    SERVICES_OK=false
else
    echo -e "${GREEN}✓${NC} Qdrant is running"
fi

# Check Neo4j
if ! nc -z localhost 7687 2>/dev/null; then
    echo -e "${RED}✗${NC} Neo4j is not running on port 7687"
    SERVICES_OK=false
else
    echo -e "${GREEN}✓${NC} Neo4j is running"
fi

# Check Graph Service
if ! nc -z localhost 50051 2>/dev/null; then
    echo -e "${RED}✗${NC} Graph Service is not running on port 50051"
    echo "  Start with: cd graph-service && go run cmd/server/main.go"
    SERVICES_OK=false
else
    echo -e "${GREEN}✓${NC} Graph Service is running"
fi

# Check Semantic Engine
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Semantic Engine is not running on port 8000"
    echo "  Start with: cd semantic-engine && source venv/bin/activate && python main.py"
    SERVICES_OK=false
else
    echo -e "${GREEN}✓${NC} Semantic Engine is running"
fi

# Check Orchestrator
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Orchestrator is not running on port 8080"
    echo "  Start with: cd orchestrator && python main.py"
    SERVICES_OK=false
else
    echo -e "${GREEN}✓${NC} Orchestrator is running"
fi

if [ "$SERVICES_OK" = false ]; then
    echo -e "\n${RED}Cannot run tests - some services are not running${NC}"
    exit 1
fi

# Step 2: Run Orchestrator Tests
echo -e "\n${YELLOW}Step 2: Running Orchestrator Unified Tests...${NC}"
echo -e "${BLUE}----------------------------------------${NC}"

if [ -f "semantic-engine/venv/bin/activate" ]; then
    source semantic-engine/venv/bin/activate
    python3 test_orchestrator.py
    TEST_EXIT_CODE=$?
else
    echo -e "${RED}Virtual environment not found${NC}"
    exit 1
fi

echo -e "\n${BLUE}========================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}  ALL TESTS PASSED!${NC}"
else
    echo -e "${RED}  SOME TESTS FAILED${NC}"
fi
echo -e "${BLUE}========================================${NC}"

exit $TEST_EXIT_CODE
