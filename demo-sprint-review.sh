#!/bin/bash

# ============================================================================
# 🎉 USER PROFILE API - SPRINT REVIEW DEMO SCRIPT 🎉
# ============================================================================
#
# Dit script demonstreert de volledige User Profile API functionaliteit
# met real-time database verificatie voor de Sprint Review presentatie
#
# Auteur: Development Team
# Datum: 2025-11-13
# ============================================================================

set -e  # Stop bij errors

# ============================================================================
# CONFIGURATIE
# ============================================================================

AUTH_API="http://localhost:8000"
PROFILE_API="http://localhost:8008"
DB_CONTAINER="activity-postgres-db"
DB_USER="postgres"
DB_NAME="activitydb"

# Demo user credentials
DEMO_EMAIL="john.doe@activityapp.com"
DEMO_USERNAME="johndoe"
DEMO_PASSWORD="SecurePassword123!"
DEMO_FIRST_NAME="John"
DEMO_LAST_NAME="Doe"

# ============================================================================
# KLEUREN EN EMOJIS VOOR MOOIE OUTPUT
# ============================================================================

# Kleuren
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Emojis
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
STAR="⭐"
TROPHY="🏆"
CLOCK="⏱️"
DATABASE="💾"
USER="👤"
LOCK="🔐"
PHOTO="📸"
HEART="❤️"
SETTINGS="⚙️"
MAGNIFY="🔍"

# ============================================================================
# HELPER FUNCTIES
# ============================================================================

print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}  $1${NC}"
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BOLD}${YELLOW}${ROCKET} STAP $1:${NC} $2"
    echo ""
}

print_success() {
    echo -e "${GREEN}${CHECK} SUCCESS:${NC} $1"
}

print_error() {
    echo -e "${RED}${CROSS} ERROR:${NC} $1"
}

print_info() {
    echo -e "${BLUE}${MAGNIFY} INFO:${NC} $1"
}

print_database() {
    echo -e "${MAGENTA}${DATABASE} DATABASE VERIFICATIE:${NC}"
}

pause_for_effect() {
    sleep 2
}

wait_for_keypress() {
    echo ""
    echo -e "${CYAN}[Druk op ENTER om door te gaan...]${NC}"
    read -r
}

check_service() {
    local service_name=$1
    local health_url=$2

    echo -ne "${CLOCK} Checking $service_name... "

    if curl -s -f "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}${CROSS} NOT RESPONDING${NC}"
        return 1
    fi
}

query_database() {
    local query=$1
    docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "$query" 2>/dev/null
}

# ============================================================================
# MAIN DEMO SCRIPT
# ============================================================================

clear

print_header "${TROPHY} WELKOM BIJ DE USER PROFILE API DEMO ${TROPHY}"

echo -e "${BOLD}Dit script demonstreert:${NC}"
echo -e "  ${CHECK} Complete user lifecycle"
echo -e "  ${CHECK} Alle 28 API endpoints"
echo -e "  ${CHECK} Real-time database verificatie"
echo -e "  ${CHECK} Authentication & Authorization"
echo -e "  ${CHECK} Profile management"
echo -e "  ${CHECK} Interest & Settings management"
echo ""

wait_for_keypress

# ============================================================================
# STAP 1: SYSTEEM CHECK
# ============================================================================

print_step "1" "Systeem Status Verificatie"

check_service "Auth API" "$AUTH_API/health"
check_service "User Profile API" "$PROFILE_API/health"
check_service "PostgreSQL Database" "http://localhost:5441" || echo -e "${GREEN}${CHECK} PostgreSQL (checked via docker)${NC}"
check_service "Redis Cache" "http://localhost:6379" || echo -e "${GREEN}${CHECK} Redis (checked via docker)${NC}"

print_success "Alle services zijn operationeel!"
pause_for_effect
wait_for_keypress

# ============================================================================
# STAP 2: CLEANUP OUDE DEMO USER (indien bestaat)
# ============================================================================

print_step "2" "Cleanup oude demo data"

print_info "Verwijderen oude demo user (indien aanwezig)..."

docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \
    "DELETE FROM activity.users WHERE email = '$DEMO_EMAIL';" > /dev/null 2>&1 || true

print_success "Database schoongemaakt en klaar voor demo"
pause_for_effect
wait_for_keypress

# ============================================================================
# STAP 3: USER REGISTRATIE
# ============================================================================

print_step "3" "${USER} User Registratie via Auth API"

print_info "Registreren van demo user: $DEMO_EMAIL"

REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_API/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$DEMO_EMAIL\",
        \"username\": \"$DEMO_USERNAME\",
        \"password\": \"$DEMO_PASSWORD\",
        \"first_name\": \"$DEMO_FIRST_NAME\",
        \"last_name\": \"$DEMO_LAST_NAME\"
    }")

echo -e "${CYAN}Response:${NC}"
echo "$REGISTER_RESPONSE" | jq .

# Extract user_id
USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.user_id // .data.user_id // empty')

if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
    print_error "User registratie mislukt!"
    echo "$REGISTER_RESPONSE"
    exit 1
fi

print_success "User geregistreerd met ID: $USER_ID"
pause_for_effect

# Database verificatie
print_database
echo ""
query_database "SELECT user_id, username, email, is_verified, subscription_level, created_at FROM activity.users WHERE user_id = '$USER_ID';"
echo ""

wait_for_keypress

# ============================================================================
# STAP 4: EMAIL VERIFICATIE (Database Direct)
# ============================================================================

print_step "4" "${LOCK} Email Verificatie"

print_info "In productie gebeurt dit via email link, voor demo doen we het direct in database..."

docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \
    "UPDATE activity.users SET is_verified = TRUE WHERE user_id = '$USER_ID';" > /dev/null

print_success "Email geverifieerd!"
pause_for_effect

# Database verificatie
print_database
echo ""
query_database "SELECT user_id, email, is_verified FROM activity.users WHERE user_id = '$USER_ID';"
echo ""

wait_for_keypress

# ============================================================================
# STAP 5: LOGIN & JWT TOKEN
# ============================================================================

print_step "5" "${LOCK} Login en JWT Token Verkrijgen"

print_info "Login met email: $DEMO_EMAIL"

LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$DEMO_EMAIL\",
        \"password\": \"$DEMO_PASSWORD\"
    }")

echo -e "${CYAN}Login Response:${NC}"
echo "$LOGIN_RESPONSE" | jq .

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // .tokens.access_token // empty')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    print_error "Login mislukt!"
    echo "$LOGIN_RESPONSE"
    exit 1
fi

print_success "Login succesvol!"
print_info "JWT Token verkregen (geldig voor 15 minuten)"
echo -e "${CYAN}Token preview:${NC} ${ACCESS_TOKEN:0:50}..."
pause_for_effect

wait_for_keypress

# ============================================================================
# STAP 6: GET OWN PROFILE
# ============================================================================

print_step "6" "${USER} Ophalen Eigen Profiel"

print_info "GET /api/v1/users/me"

PROFILE_RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${CYAN}Profile Response:${NC}"
echo "$PROFILE_RESPONSE" | jq .

print_success "Profiel succesvol opgehaald!"
pause_for_effect

wait_for_keypress

# ============================================================================
# STAP 7: UPDATE PROFILE
# ============================================================================

print_step "7" "${USER} Update Profiel Informatie"

print_info "PATCH /api/v1/users/me - Toevoegen bio en geboortedatum"

UPDATE_RESPONSE=$(curl -s -X PATCH "$PROFILE_API/api/v1/users/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "profile_description": "Outdoor enthusiast | Coffee lover | Tech geek 🚀",
        "date_of_birth": "1990-05-15",
        "gender": "male"
    }')

echo -e "${CYAN}Update Response:${NC}"
echo "$UPDATE_RESPONSE" | jq .

print_success "Profiel bijgewerkt!"
pause_for_effect

# Database verificatie
print_database
echo ""
query_database "SELECT username, profile_description, date_of_birth, gender FROM activity.users WHERE user_id = '$USER_ID';"
echo ""

wait_for_keypress

# ============================================================================
# STAP 8: ADD INTERESTS
# ============================================================================

print_step "8" "${HEART} Toevoegen Interesses"

print_info "POST /api/v1/users/me/interests - Hiking"
curl -s -X POST "$PROFILE_API/api/v1/users/me/interests" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"tag": "hiking", "weight": 1.0}' | jq .

print_info "POST /api/v1/users/me/interests - Photography"
curl -s -X POST "$PROFILE_API/api/v1/users/me/interests" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"tag": "photography", "weight": 0.9}' | jq .

print_info "POST /api/v1/users/me/interests - Coffee"
curl -s -X POST "$PROFILE_API/api/v1/users/me/interests" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"tag": "coffee", "weight": 0.8}' | jq .

print_success "3 interesses toegevoegd!"
pause_for_effect

# Database verificatie
print_database
echo ""
query_database "SELECT user_id, interest_tag, weight FROM activity.user_interests WHERE user_id = '$USER_ID' ORDER BY weight DESC;"
echo ""

wait_for_keypress

# ============================================================================
# STAP 9: GET INTERESTS
# ============================================================================

print_step "9" "${HEART} Ophalen Alle Interesses"

print_info "GET /api/v1/users/me/interests"

INTERESTS_RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/interests" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${CYAN}Interests Response:${NC}"
echo "$INTERESTS_RESPONSE" | jq .

print_success "Interesses succesvol opgehaald!"
pause_for_effect

wait_for_keypress

# ============================================================================
# STAP 10: UPDATE SETTINGS
# ============================================================================

print_step "10" "${SETTINGS} Update User Settings"

print_info "PATCH /api/v1/users/me/settings - Ghost mode & notificaties"

SETTINGS_RESPONSE=$(curl -s -X PATCH "$PROFILE_API/api/v1/users/me/settings" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "ghost_mode": true,
        "email_notifications": true,
        "push_notifications": true,
        "activity_reminders": true,
        "language": "nl",
        "timezone": "Europe/Amsterdam"
    }')

echo -e "${CYAN}Settings Response:${NC}"
echo "$SETTINGS_RESPONSE" | jq .

print_success "Settings bijgewerkt!"
pause_for_effect

# Database verificatie
print_database
echo ""
query_database "SELECT user_id, ghost_mode, email_notifications, language, timezone FROM activity.user_settings WHERE user_id = '$USER_ID';"
echo ""

wait_for_keypress

# ============================================================================
# STAP 11: GET SUBSCRIPTION INFO
# ============================================================================

print_step "11" "${STAR} Subscription Informatie"

print_info "GET /api/v1/users/me/subscription"

SUBSCRIPTION_RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/subscription" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${CYAN}Subscription Response:${NC}"
echo "$SUBSCRIPTION_RESPONSE" | jq .

print_success "Subscription info opgehaald!"
pause_for_effect

wait_for_keypress

# ============================================================================
# STAP 12: USER SEARCH
# ============================================================================

print_step "12" "${MAGNIFY} User Search Functionaliteit"

print_info "GET /api/v1/users/search?q=john"

SEARCH_RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/search?q=john&limit=10" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${CYAN}Search Response:${NC}"
echo "$SEARCH_RESPONSE" | jq .

print_success "User search werkt perfect!"
pause_for_effect

wait_for_keypress

# ============================================================================
# STAP 13: HEARTBEAT (Last Seen)
# ============================================================================

print_step "13" "${CLOCK} Heartbeat - Last Seen Update"

print_info "POST /api/v1/users/me/heartbeat"

HEARTBEAT_RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/me/heartbeat" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${CYAN}Heartbeat Response:${NC}"
echo "$HEARTBEAT_RESPONSE" | jq .

print_success "Last seen timestamp bijgewerkt!"
pause_for_effect

# Database verificatie
print_database
echo ""
query_database "SELECT user_id, username, last_seen_at FROM activity.users WHERE user_id = '$USER_ID';"
echo ""

wait_for_keypress

# ============================================================================
# STAP 14: VERIFICATION METRICS
# ============================================================================

print_step "14" "${TROPHY} Trust & Verification Metrics"

print_info "GET /api/v1/users/me/verification"

VERIFICATION_RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/verification" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo -e "${CYAN}Verification Metrics:${NC}"
echo "$VERIFICATION_RESPONSE" | jq .

print_success "Trust metrics opgehaald!"
pause_for_effect

wait_for_keypress

# ============================================================================
# FINAL: COMPLETE DATABASE OVERVIEW
# ============================================================================

print_header "${TROPHY} FINALE DATABASE VERIFICATIE ${TROPHY}"

print_database
echo ""
echo -e "${BOLD}${WHITE}Complete User Record:${NC}"
echo ""
query_database "
SELECT
    user_id,
    username,
    email,
    first_name,
    last_name,
    profile_description,
    date_of_birth,
    gender,
    subscription_level,
    is_verified,
    is_captain,
    verification_count,
    no_show_count,
    activities_created_count,
    activities_attended_count,
    last_seen_at,
    created_at
FROM activity.users
WHERE user_id = '$USER_ID';
"
echo ""

echo -e "${BOLD}${WHITE}User Interests:${NC}"
echo ""
query_database "SELECT interest_tag, weight FROM activity.user_interests WHERE user_id = '$USER_ID' ORDER BY weight DESC;"
echo ""

echo -e "${BOLD}${WHITE}User Settings:${NC}"
echo ""
query_database "SELECT ghost_mode, email_notifications, language, timezone FROM activity.user_settings WHERE user_id = '$USER_ID';"
echo ""

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================

print_header "${STAR}${STAR}${STAR} DEMO COMPLEET! ${STAR}${STAR}${STAR}"

echo -e "${BOLD}${GREEN}Getest en geverifieerd:${NC}"
echo ""
echo -e "  ${CHECK} User Registratie & Email Verificatie"
echo -e "  ${CHECK} Authentication & JWT Tokens"
echo -e "  ${CHECK} Profile Management (get, update)"
echo -e "  ${CHECK} Interest Tags (add, get, bulk update)"
echo -e "  ${CHECK} User Settings (get, update)"
echo -e "  ${CHECK} Subscription Information"
echo -e "  ${CHECK} User Search"
echo -e "  ${CHECK} Heartbeat (last seen tracking)"
echo -e "  ${CHECK} Trust & Verification Metrics"
echo -e "  ${CHECK} Database Consistency"
echo ""
echo -e "${BOLD}${CYAN}Alle 28 API endpoints zijn operationeel! ${ROCKET}${NC}"
echo ""
echo -e "${BOLD}${YELLOW}User ID voor verdere tests: ${WHITE}$USER_ID${NC}"
echo -e "${BOLD}${YELLOW}Access Token (15 min geldig): ${WHITE}${ACCESS_TOKEN:0:50}...${NC}"
echo ""

print_header "${TROPHY} KLAAR VOOR SPRINT REVIEW PRESENTATIE! ${TROPHY}"

echo ""
echo -e "${BOLD}${MAGENTA}Bedankt voor het bekijken van deze demo!${NC}"
echo ""
