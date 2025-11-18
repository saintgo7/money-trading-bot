#!/bin/bash

# Performance benchmark script for Money Trading Bot

echo "========================================="
echo "Money Trading Bot - Performance Benchmark"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if services are running
echo "Checking if services are running..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}Error: Services are not running. Please start with 'docker-compose up -d'${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Services are running${NC}"
echo ""

# 1. Run unit tests
echo "1. Running unit tests..."
docker-compose exec -T backend pytest tests/ -v --tb=short --maxfail=5
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
fi
echo ""

# 2. Run integration tests
echo "2. Running integration tests..."
docker-compose exec -T backend pytest tests/test_integration.py -v
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
fi
echo ""

# 3. Run performance tests
echo "3. Running performance tests..."
docker-compose exec -T backend pytest tests/test_performance.py -v
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Performance tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Performance tests have issues${NC}"
fi
echo ""

# 4. Check API response time
echo "4. Testing API response time..."
START_TIME=$(date +%s%N)
curl -s http://localhost:8000/health > /dev/null
END_TIME=$(date +%s%N)
ELAPSED=$((($END_TIME - $START_TIME) / 1000000))
echo "Health endpoint response time: ${ELAPSED}ms"
if [ $ELAPSED -lt 100 ]; then
    echo -e "${GREEN}✓ Response time is good (<100ms)${NC}"
elif [ $ELAPSED -lt 500 ]; then
    echo -e "${YELLOW}⚠ Response time is acceptable (100-500ms)${NC}"
else
    echo -e "${RED}✗ Response time is slow (>500ms)${NC}"
fi
echo ""

# 5. Check database performance
echo "5. Testing database performance..."
docker-compose exec -T postgres psql -U user -d trading_bot -c "
EXPLAIN ANALYZE SELECT * FROM trading_bots LIMIT 100;
" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database is responsive${NC}"
else
    echo -e "${RED}✗ Database has issues${NC}"
fi
echo ""

# 6. Check Redis performance
echo "6. Testing Redis performance..."
REDIS_PING=$(docker-compose exec -T redis redis-cli ping)
if [ "$REDIS_PING" == "PONG" ]; then
    echo -e "${GREEN}✓ Redis is responsive${NC}"
else
    echo -e "${RED}✗ Redis has issues${NC}"
fi
echo ""

# 7. Memory usage
echo "7. Checking memory usage..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep trading_bot
echo ""

# 8. Load test (optional)
if command -v locust &> /dev/null; then
    echo "8. Running load test..."
    echo "Starting locust on http://localhost:8089"
    echo "Run: locust -f backend/tests/locustfile.py --host=http://localhost:8000"
    echo "Then open http://localhost:8089 in your browser to start the test"
else
    echo "8. Skipping load test (locust not installed)"
    echo "Install with: pip install locust"
fi
echo ""

# 9. Generate performance report
echo "========================================="
echo "Performance Summary"
echo "========================================="
echo "Run timestamp: $(date)"
echo ""
echo "Next steps:"
echo "1. Review test results above"
echo "2. Check logs: docker-compose logs"
echo "3. Monitor in real-time: docker stats"
echo "4. Run load tests with locust for production readiness"
echo ""
echo -e "${GREEN}Benchmark complete!${NC}"
