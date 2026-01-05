#!/bin/bash
# Deployment script for ML Car Price Prediction
# Usage: ./deploy.sh [dev|sit|uat|prod] [up|down|restart|logs]

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENV="${1:-dev}"
ACTION="${2:-up}"

# Validate environment
if [[ ! "$ENV" =~ ^(dev|sit|uat|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment '$ENV'${NC}"
    echo "Usage: $0 [dev|sit|uat|prod] [up|down|restart|logs|status]"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(up|down|restart|logs|status|scale|backup)$ ]]; then
    echo -e "${RED}Error: Invalid action '$ACTION'${NC}"
    echo "Valid actions: up, down, restart, logs, status, scale, backup"
    exit 1
fi

COMPOSE_FILE="deployment/$ENV/docker-compose.$ENV.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: Compose file not found: $COMPOSE_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ML Car Price Prediction - Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${YELLOW}$ENV${NC}"
echo -e "Action: ${YELLOW}$ACTION${NC}"
echo -e "${GREEN}========================================${NC}"

case $ACTION in
    up)
        echo -e "${YELLOW}Starting services...${NC}"
        
        # Production requires secrets
        if [ "$ENV" = "prod" ]; then
            if [ -z "$PROD_DB_PASSWORD" ] || [ -z "$REDIS_PASSWORD" ]; then
                echo -e "${RED}Error: Production secrets not set!${NC}"
                echo "Please export: PROD_DB_PASSWORD, REDIS_PASSWORD, JWT_SECRET"
                exit 1
            fi
            
            # Check SSL certificates
            if [ ! -f "deployment/prod/ssl/cert.pem" ]; then
                echo -e "${YELLOW}SSL certificates not found. Generating...${NC}"
                ./scripts/generate_ssl_certs.sh
            fi
        fi
        
        docker-compose -f "$COMPOSE_FILE" up --build -d
        echo -e "${GREEN}Services started successfully!${NC}"
        
        # Show service URLs
        case $ENV in
            dev)
                echo -e "\n${GREEN}Access services:${NC}"
                echo "  - MLflow: http://localhost:5000"
                echo "  - API: http://localhost:8000"
                echo "  - UI: http://localhost:8501"
                ;;
            sit)
                echo -e "\n${GREEN}Access services:${NC}"
                echo "  - MLflow: http://localhost:5001"
                echo "  - API: http://localhost:8001"
                echo "  - UI: http://localhost:8502"
                ;;
            uat)
                echo -e "\n${GREEN}Access services:${NC}"
                echo "  - API: http://localhost/api"
                echo "  - UI: http://localhost/"
                echo "  - MLflow: http://localhost:5002"
                ;;
            prod)
                echo -e "\n${GREEN}Access services:${NC}"
                echo "  - HTTPS: https://localhost/"
                echo "  - Grafana: http://localhost:3000"
                echo "  - Prometheus: http://localhost:9090"
                ;;
        esac
        ;;
        
    down)
        echo -e "${YELLOW}Stopping services...${NC}"
        docker-compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}Services stopped successfully!${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting services...${NC}"
        docker-compose -f "$COMPOSE_FILE" restart
        echo -e "${GREEN}Services restarted successfully!${NC}"
        ;;
        
    logs)
        SERVICE="${3:-}"
        if [ -n "$SERVICE" ]; then
            docker-compose -f "$COMPOSE_FILE" logs -f --tail=100 "$SERVICE"
        else
            docker-compose -f "$COMPOSE_FILE" logs -f --tail=100
        fi
        ;;
        
    status)
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
        
    scale)
        if [ "$ENV" != "prod" ]; then
            echo -e "${RED}Error: Scaling only available for production${NC}"
            exit 1
        fi
        REPLICAS="${3:-3}"
        echo -e "${YELLOW}Scaling API to $REPLICAS instances...${NC}"
        docker-compose -f "$COMPOSE_FILE" up --scale api="$REPLICAS" -d
        echo -e "${GREEN}API scaled successfully!${NC}"
        ;;
        
    backup)
        BACKUP_FILE="backup_${ENV}_$(date +%Y%m%d_%H%M%S).sql"
        echo -e "${YELLOW}Creating database backup: $BACKUP_FILE${NC}"
        
        case $ENV in
            dev) DB_USER="ml_user" ;;
            sit) DB_USER="ml_user_sit" ;;
            uat) DB_USER="ml_user_uat" ;;
            prod) DB_USER="ml_user_prod" ;;
        esac
        
        docker-compose -f "$COMPOSE_FILE" exec -T postgres \
            pg_dump -U "$DB_USER" ml_evaluation > "$BACKUP_FILE"
        
        echo -e "${GREEN}Backup created: $BACKUP_FILE${NC}"
        ;;
        
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        exit 1
        ;;
esac
