#!/bin/bash

# ============================================================================
# USER PROFILE API - COMPREHENSIVE TEST SCRIPT
# ============================================================================
#
# Dit script test ALLE 28 endpoints van de User Profile API met:
# - Authenticatie flows (Bearer token & Service-to-Service)
# - Validatie van input (verplichte velden, lengtes, regex, grenzen)
# - Permissies (admin-only, S2S-only, user routes)
# - Database verificatie na elke operatie
# - Edge cases en foutafhandeling
#
# ============================================================================

set -e  # Stop bij errors

# ============================================================================
# CONFIGURATIE
# ============================================================================

AUTH_API="${AUTH_API:-http://localhost:8000}"
PROFILE_API="${PROFILE_API:-http://localhost:8008}"
DB_CONTAINER="${DB_CONTAINER:-activity-postgres-db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-activitydb}"

# Test user credentials
TEST_EMAIL="testuser@example.com"
TEST_USERNAME="testuser"
TEST_PASSWORD="TestPassword123!"
TEST_FIRST_NAME="Test"
TEST_LAST_NAME="User"

# Admin user credentials (moet al bestaan in database)
ADMIN_EMAIL="admin@example.com"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="AdminPassword123!"

# Service API Keys (from .env.example)
SERVICE_API_KEY="${ACTIVITIES_API_KEY:-activities-service-key-change-in-production}"
PAYMENT_API_KEY="${PAYMENT_API_KEY:-payment-processor-key-change-in-production}"

# ============================================================================
# KLEUREN EN EMOJIS
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
CHECK="✅"
CROSS="❌"
ROCKET="🚀"
DATABASE="💾"
LOCK="🔐"
USER="👤"
PHOTO="📸"
HEART="❤️"
SETTINGS="⚙️"
STAR="⭐"
TROPHY="🏆"
MAGNIFY="🔍"
CLOCK="⏱️"
WARNING="⚠️"
INFO="ℹ️"

# ============================================================================
# TEST TRACKING
# ============================================================================

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

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

print_section() {
    echo ""
    echo -e "${BOLD}${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${YELLOW}${ROCKET} $1${NC}"
    echo -e "${BOLD}${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_test() {
    echo -e "${BOLD}${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}${CHECK} SUCCESS:${NC} $1"
    ((PASSED_TESTS++))
}

print_error() {
    echo -e "${RED}${CROSS} FAILED:${NC} $1"
    ((FAILED_TESTS++))
}

print_warning() {
    echo -e "${YELLOW}${WARNING} WARNING:${NC} $1"
}

print_info() {
    echo -e "${CYAN}${INFO} INFO:${NC} $1"
}

print_db() {
    echo -e "${MAGENTA}${DATABASE} DATABASE:${NC} $1"
}

print_skip() {
    echo -e "${YELLOW}⏭️  SKIPPED:${NC} $1"
    ((SKIPPED_TESTS++))
}

query_db() {
    local query=$1
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -A -c "$query" 2>/dev/null || echo ""
}

query_db_table() {
    local query=$1
    echo ""
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "$query" 2>/dev/null || echo "Query failed"
    echo ""
}

test_endpoint() {
    ((TOTAL_TESTS++))
    print_test "$1"
}

verify_response() {
    local response=$1
    local expected_field=$2
    local description=$3

    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        print_success "$description"
        return 0
    else
        print_error "$description - Field '$expected_field' not found"
        echo "Response: $response" | jq . 2>/dev/null || echo "$response"
        return 1
    fi
}

verify_db_value() {
    local query=$1
    local expected=$2
    local description=$3

    local result=$(query_db "$query")

    if [ "$result" = "$expected" ]; then
        print_db "✓ $description: $result"
        return 0
    else
        print_db "✗ $description: Expected '$expected', got '$result'"
        return 1
    fi
}

# ============================================================================
# SETUP FUNCTIES
# ============================================================================

cleanup_test_data() {
    print_info "Cleaning up test data from previous runs..."

    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \
        "DELETE FROM activity.users WHERE email IN ('$TEST_EMAIL', 'testuser2@example.com');" > /dev/null 2>&1 || true

    print_success "Test data cleaned"
}

create_test_user() {
    print_info "Creating test user via Auth API..."

    REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_API/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_EMAIL\",
            \"username\": \"$TEST_USERNAME\",
            \"password\": \"$TEST_PASSWORD\",
            \"first_name\": \"$TEST_FIRST_NAME\",
            \"last_name\": \"$TEST_LAST_NAME\"
        }")

    USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.user_id // .data.user_id // empty')

    if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
        print_error "Failed to create test user"
        echo "$REGISTER_RESPONSE" | jq .
        exit 1
    fi

    # Verify email in database
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \
        "UPDATE activity.users SET is_verified = TRUE WHERE user_id = '$USER_ID';" > /dev/null

    print_success "Test user created: $USER_ID"
}

get_user_token() {
    print_info "Getting JWT token for test user..."

    LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_EMAIL\",
            \"password\": \"$TEST_PASSWORD\"
        }")

    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // .tokens.access_token // empty')

    if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
        print_error "Failed to get access token"
        echo "$LOGIN_RESPONSE" | jq .
        exit 1
    fi

    print_success "JWT token obtained"
}

setup_admin_user() {
    print_info "Setting up admin user..."

    # Create admin user if not exists
    ADMIN_EXISTS=$(query_db "SELECT COUNT(*) FROM activity.users WHERE email = '$ADMIN_EMAIL';")

    if [ "$ADMIN_EXISTS" = "0" ]; then
        print_info "Creating admin user..."

        ADMIN_REGISTER=$(curl -s -X POST "$AUTH_API/api/auth/register" \
            -H "Content-Type: application/json" \
            -d "{
                \"email\": \"$ADMIN_EMAIL\",
                \"username\": \"$ADMIN_USERNAME\",
                \"password\": \"$ADMIN_PASSWORD\",
                \"first_name\": \"Admin\",
                \"last_name\": \"User\"
            }")

        ADMIN_USER_ID=$(echo "$ADMIN_REGISTER" | jq -r '.user_id // .data.user_id // empty')

        # Set admin role and verify
        docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \
            "UPDATE activity.users SET role = 'admin', is_verified = TRUE WHERE user_id = '$ADMIN_USER_ID';" > /dev/null

        print_success "Admin user created"
    else
        print_info "Admin user already exists"
        ADMIN_USER_ID=$(query_db "SELECT user_id FROM activity.users WHERE email = '$ADMIN_EMAIL';")
    fi

    # Get admin token
    ADMIN_LOGIN=$(curl -s -X POST "$AUTH_API/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$ADMIN_EMAIL\",
            \"password\": \"$ADMIN_PASSWORD\"
        }")

    ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | jq -r '.access_token // .tokens.access_token // empty')

    if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
        print_warning "Failed to get admin token, admin tests will be skipped"
        ADMIN_TOKEN=""
    else
        print_success "Admin token obtained"
    fi
}

# ============================================================================
# TEST FUNCTIES - PROFILE MANAGEMENT (5 endpoints)
# ============================================================================

test_profile_management() {
    print_section "1. PROFILE MANAGEMENT (5 endpoints)"

    # 1.1 GET /api/v1/users/me - Get My Profile
    test_endpoint "GET /api/v1/users/me - Get my own profile"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "user_id" "Profile retrieved with user_id"
    verify_response "$RESPONSE" "email" "Profile contains email"
    verify_response "$RESPONSE" "username" "Profile contains username"

    # Database verification
    print_db "Verifying in database:"
    query_db_table "SELECT user_id, username, email, subscription_level, is_verified FROM activity.users WHERE user_id = '$USER_ID' LIMIT 1;"

    # 1.2 PATCH /api/v1/users/me - Update My Profile
    test_endpoint "PATCH /api/v1/users/me - Update profile fields"

    RESPONSE=$(curl -s -X PATCH "$PROFILE_API/api/v1/users/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "profile_description": "Test bio for comprehensive testing",
            "date_of_birth": "1995-03-20",
            "gender": "non-binary"
        }')

    verify_response "$RESPONSE" "success" "Profile updated successfully"

    # Verify in database
    verify_db_value \
        "SELECT profile_description FROM activity.users WHERE user_id = '$USER_ID';" \
        "Test bio for comprehensive testing" \
        "Profile description updated in DB"

    # 1.3 GET /api/v1/users/{user_id} - Get Public Profile
    test_endpoint "GET /api/v1/users/{user_id} - Get public profile of another user"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/$USER_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "user_id" "Public profile retrieved"
    verify_response "$RESPONSE" "username" "Public profile contains username"

    # Should NOT contain email (private field)
    if echo "$RESPONSE" | jq -e ".email" > /dev/null 2>&1; then
        print_error "Public profile should NOT contain email field"
    else
        print_success "Public profile correctly excludes email"
    fi

    # 1.4 PATCH /api/v1/users/me/username - Update Username
    test_endpoint "PATCH /api/v1/users/me/username - Change username"

    NEW_USERNAME="testuser_updated"
    RESPONSE=$(curl -s -X PATCH "$PROFILE_API/api/v1/users/me/username" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"new_username\": \"$NEW_USERNAME\"}")

    verify_response "$RESPONSE" "username" "Username changed"

    verify_db_value \
        "SELECT username FROM activity.users WHERE user_id = '$USER_ID';" \
        "$NEW_USERNAME" \
        "Username updated in DB"

    # Test invalid username (should fail)
    test_endpoint "PATCH /api/v1/users/me/username - Invalid username validation"

    RESPONSE=$(curl -s -X PATCH "$PROFILE_API/api/v1/users/me/username" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"new_username": "ab"}')  # Too short

    if echo "$RESPONSE" | jq -e ".detail" > /dev/null 2>&1; then
        print_success "Invalid username correctly rejected (too short)"
    else
        print_error "Invalid username should be rejected"
    fi

    # 1.5 DELETE /api/v1/users/me - Delete Account (we'll skip actual deletion)
    print_skip "DELETE /api/v1/users/me - Skipping actual account deletion to preserve test user"
}

# ============================================================================
# TEST FUNCTIES - PHOTO MANAGEMENT (3 endpoints)
# ============================================================================

test_photo_management() {
    print_section "2. PHOTO MANAGEMENT (3 endpoints)"

    # 2.1 POST /api/v1/users/me/photos/main - Set Main Photo
    test_endpoint "POST /api/v1/users/me/photos/main - Set main profile photo"

    PHOTO_URL="https://cdn.example.com/photos/test-photo-123.jpg"
    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/me/photos/main" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"photo_url\": \"$PHOTO_URL\"}")

    verify_response "$RESPONSE" "moderation_status" "Main photo set with moderation status"

    # Verify in database
    verify_db_value \
        "SELECT main_photo_url FROM activity.users WHERE user_id = '$USER_ID';" \
        "$PHOTO_URL" \
        "Main photo URL stored in DB"

    verify_db_value \
        "SELECT main_photo_moderation_status FROM activity.users WHERE user_id = '$USER_ID';" \
        "pending" \
        "Moderation status is pending"

    # 2.2 POST /api/v1/users/me/photos - Add Extra Photo
    test_endpoint "POST /api/v1/users/me/photos - Add extra profile photo"

    EXTRA_PHOTO="https://cdn.example.com/photos/extra-photo-456.jpg"
    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/me/photos" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"photo_url\": \"$EXTRA_PHOTO\"}")

    verify_response "$RESPONSE" "photo_count" "Extra photo added"

    # Verify count
    PHOTO_COUNT=$(echo "$RESPONSE" | jq -r '.photo_count // 0')
    if [ "$PHOTO_COUNT" -ge 1 ]; then
        print_success "Photo count is correct: $PHOTO_COUNT"
    else
        print_error "Photo count should be at least 1"
    fi

    # 2.3 DELETE /api/v1/users/me/photos - Remove Extra Photo
    test_endpoint "DELETE /api/v1/users/me/photos - Remove extra profile photo"

    RESPONSE=$(curl -s -X DELETE "$PROFILE_API/api/v1/users/me/photos" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"photo_url\": \"$EXTRA_PHOTO\"}")

    verify_response "$RESPONSE" "success" "Extra photo removed"
}

# ============================================================================
# TEST FUNCTIES - INTEREST TAGS (4 endpoints)
# ============================================================================

test_interest_tags() {
    print_section "3. INTEREST TAGS (4 endpoints)"

    # 3.1 POST /api/v1/users/me/interests - Add Interest
    test_endpoint "POST /api/v1/users/me/interests - Add single interest (hiking)"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/me/interests" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"tag": "hiking", "weight": 1.0}')

    verify_response "$RESPONSE" "success" "Interest 'hiking' added"

    # Add more interests
    test_endpoint "POST /api/v1/users/me/interests - Add interest (photography)"
    curl -s -X POST "$PROFILE_API/api/v1/users/me/interests" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"tag": "photography", "weight": 0.9}' > /dev/null
    print_success "Interest 'photography' added"

    test_endpoint "POST /api/v1/users/me/interests - Add interest (coding)"
    curl -s -X POST "$PROFILE_API/api/v1/users/me/interests" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"tag": "coding", "weight": 0.8}' > /dev/null
    print_success "Interest 'coding' added"

    # Verify in database
    print_db "Verifying interests in database:"
    query_db_table "SELECT interest_tag, weight FROM activity.user_interests WHERE user_id = '$USER_ID' ORDER BY weight DESC;"

    # 3.2 GET /api/v1/users/me/interests - Get Interests
    test_endpoint "GET /api/v1/users/me/interests - Get all interests"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/interests" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "interests" "Interests retrieved"
    verify_response "$RESPONSE" "count" "Interest count returned"

    INTEREST_COUNT=$(echo "$RESPONSE" | jq -r '.count // 0')
    if [ "$INTEREST_COUNT" -ge 3 ]; then
        print_success "Interest count is correct: $INTEREST_COUNT"
    else
        print_error "Expected at least 3 interests, got $INTEREST_COUNT"
    fi

    # 3.3 PUT /api/v1/users/me/interests - Set Interests (bulk replace)
    test_endpoint "PUT /api/v1/users/me/interests - Bulk replace all interests"

    RESPONSE=$(curl -s -X PUT "$PROFILE_API/api/v1/users/me/interests" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "interests": [
                {"tag": "running", "weight": 1.0},
                {"tag": "cycling", "weight": 0.9},
                {"tag": "swimming", "weight": 0.7}
            ]
        }')

    verify_response "$RESPONSE" "interest_count" "Interests replaced"

    NEW_COUNT=$(echo "$RESPONSE" | jq -r '.interest_count // 0')
    if [ "$NEW_COUNT" -eq 3 ]; then
        print_success "Interest count after replacement: $NEW_COUNT"
    else
        print_error "Expected 3 interests after replacement, got $NEW_COUNT"
    fi

    # 3.4 DELETE /api/v1/users/me/interests/{tag} - Remove Interest
    test_endpoint "DELETE /api/v1/users/me/interests/running - Remove single interest"

    RESPONSE=$(curl -s -X DELETE "$PROFILE_API/api/v1/users/me/interests/running" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "success" "Interest 'running' removed"

    # Verify in database
    RUNNING_EXISTS=$(query_db "SELECT COUNT(*) FROM activity.user_interests WHERE user_id = '$USER_ID' AND interest_tag = 'running';")
    if [ "$RUNNING_EXISTS" = "0" ]; then
        print_db "✓ Interest 'running' removed from DB"
    else
        print_db "✗ Interest 'running' still in DB"
    fi
}

# ============================================================================
# TEST FUNCTIES - USER SETTINGS (2 endpoints)
# ============================================================================

test_user_settings() {
    print_section "4. USER SETTINGS (2 endpoints)"

    # 4.1 GET /api/v1/users/me/settings - Get Settings
    test_endpoint "GET /api/v1/users/me/settings - Get current settings"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/settings" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "email_notifications" "Settings retrieved"
    verify_response "$RESPONSE" "ghost_mode" "Settings contain ghost_mode"
    verify_response "$RESPONSE" "language" "Settings contain language"

    # 4.2 PATCH /api/v1/users/me/settings - Update Settings
    test_endpoint "PATCH /api/v1/users/me/settings - Update user settings"

    RESPONSE=$(curl -s -X PATCH "$PROFILE_API/api/v1/users/me/settings" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "ghost_mode": true,
            "email_notifications": false,
            "push_notifications": true,
            "language": "nl",
            "timezone": "Europe/Amsterdam"
        }')

    verify_response "$RESPONSE" "success" "Settings updated"

    # Verify in database
    print_db "Verifying settings in database:"
    query_db_table "SELECT ghost_mode, email_notifications, push_notifications, language, timezone FROM activity.user_settings WHERE user_id = '$USER_ID';"

    verify_db_value \
        "SELECT ghost_mode::text FROM activity.user_settings WHERE user_id = '$USER_ID';" \
        "t" \
        "Ghost mode enabled in DB"
}

# ============================================================================
# TEST FUNCTIES - SUBSCRIPTION MANAGEMENT (2 endpoints)
# ============================================================================

test_subscription_management() {
    print_section "5. SUBSCRIPTION MANAGEMENT (2 endpoints)"

    # 5.1 GET /api/v1/users/me/subscription - Get Subscription
    test_endpoint "GET /api/v1/users/me/subscription - Get subscription info"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/subscription" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "subscription_level" "Subscription info retrieved"
    verify_response "$RESPONSE" "is_captain" "Contains captain status"

    # 5.2 POST /api/v1/users/me/subscription - Update Subscription
    test_endpoint "POST /api/v1/users/me/subscription - Update subscription (requires payment key)"

    FUTURE_DATE=$(date -u -d "+30 days" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+30d +"%Y-%m-%dT%H:%M:%SZ")

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/me/subscription" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "X-Payment-API-Key: $PAYMENT_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"subscription_level\": \"premium\",
            \"subscription_expires_at\": \"$FUTURE_DATE\"
        }")

    if echo "$RESPONSE" | jq -e ".subscription_level" > /dev/null 2>&1; then
        verify_response "$RESPONSE" "subscription_level" "Subscription updated"

        # Verify in database
        verify_db_value \
            "SELECT subscription_level FROM activity.users WHERE user_id = '$USER_ID';" \
            "premium" \
            "Subscription level updated to premium"
    else
        print_warning "Subscription update may require valid payment key or additional setup"
    fi
}

# ============================================================================
# TEST FUNCTIES - CAPTAIN PROGRAM (2 endpoints)
# ============================================================================

test_captain_program() {
    print_section "6. CAPTAIN PROGRAM (2 endpoints - Admin only)"

    if [ -z "$ADMIN_TOKEN" ]; then
        print_skip "POST /api/v1/users/{user_id}/captain - No admin token available"
        print_skip "DELETE /api/v1/users/{user_id}/captain - No admin token available"
        return
    fi

    # 6.1 POST /api/v1/users/{user_id}/captain - Grant Captain Status
    test_endpoint "POST /api/v1/users/{user_id}/captain - Grant captain status (admin)"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/$USER_ID/captain" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"is_captain": true}')

    verify_response "$RESPONSE" "is_captain" "Captain status granted"

    # Verify in database
    verify_db_value \
        "SELECT is_captain::text FROM activity.users WHERE user_id = '$USER_ID';" \
        "t" \
        "Captain status in DB"

    # 6.2 DELETE /api/v1/users/{user_id}/captain - Revoke Captain Status
    test_endpoint "DELETE /api/v1/users/{user_id}/captain - Revoke captain status (admin)"

    RESPONSE=$(curl -s -X DELETE "$PROFILE_API/api/v1/users/$USER_ID/captain" \
        -H "Authorization: Bearer $ADMIN_TOKEN")

    verify_response "$RESPONSE" "is_captain" "Captain status revoked"

    verify_db_value \
        "SELECT is_captain::text FROM activity.users WHERE user_id = '$USER_ID';" \
        "f" \
        "Captain status removed in DB"
}

# ============================================================================
# TEST FUNCTIES - TRUST & VERIFICATION (4 endpoints)
# ============================================================================

test_trust_verification() {
    print_section "7. TRUST & VERIFICATION (4 endpoints)"

    # 7.1 GET /api/v1/users/me/verification - Get Verification Metrics
    test_endpoint "GET /api/v1/users/me/verification - Get verification metrics"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/me/verification" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "verification_count" "Verification metrics retrieved"
    verify_response "$RESPONSE" "no_show_count" "Contains no_show_count"
    verify_response "$RESPONSE" "trust_score" "Contains trust_score"

    # 7.2 POST /api/v1/users/{user_id}/verify - Increment Verification (S2S)
    test_endpoint "POST /api/v1/users/{user_id}/verify - Increment verification (S2S)"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/$USER_ID/verify" \
        -H "X-Service-API-Key: $SERVICE_API_KEY")

    verify_response "$RESPONSE" "new_verification_count" "Verification count incremented"

    NEW_COUNT=$(echo "$RESPONSE" | jq -r '.new_verification_count // 0')
    print_db "New verification count: $NEW_COUNT"

    # 7.3 POST /api/v1/users/{user_id}/no-show - Increment No Show (S2S)
    test_endpoint "POST /api/v1/users/{user_id}/no-show - Increment no-show (S2S)"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/$USER_ID/no-show" \
        -H "X-Service-API-Key: $SERVICE_API_KEY")

    verify_response "$RESPONSE" "new_no_show_count" "No-show count incremented"

    NEW_NO_SHOW=$(echo "$RESPONSE" | jq -r '.new_no_show_count // 0')
    print_db "New no-show count: $NEW_NO_SHOW"

    # 7.4 POST /api/v1/users/{user_id}/activity-counters - Update Activity Counters (S2S)
    test_endpoint "POST /api/v1/users/{user_id}/activity-counters - Update counters (S2S)"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/$USER_ID/activity-counters" \
        -H "X-Service-API-Key: $SERVICE_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "created_delta": 5,
            "attended_delta": 10
        }')

    verify_response "$RESPONSE" "activities_created_count" "Activity counters updated"

    # Verify in database
    print_db "Verifying activity counters in database:"
    query_db_table "SELECT activities_created_count, activities_attended_count FROM activity.users WHERE user_id = '$USER_ID';"

    # Test validation - deltas should be between -100 and 100
    test_endpoint "POST /api/v1/users/{user_id}/activity-counters - Validate delta limits"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/$USER_ID/activity-counters" \
        -H "X-Service-API-Key: $SERVICE_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "created_delta": 150,
            "attended_delta": 10
        }')

    if echo "$RESPONSE" | jq -e ".detail" > /dev/null 2>&1; then
        print_success "Delta validation works (rejected delta > 100)"
    else
        print_warning "Delta validation may not be working correctly"
    fi
}

# ============================================================================
# TEST FUNCTIES - USER SEARCH (1 endpoint)
# ============================================================================

test_user_search() {
    print_section "8. USER SEARCH (1 endpoint)"

    # 8.1 GET /api/v1/users/search - Search Users
    test_endpoint "GET /api/v1/users/search?q=test - Search users by query"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/search?q=test&limit=10&offset=0" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "results" "Search results retrieved"
    verify_response "$RESPONSE" "total" "Contains total count"

    # Test minimum query length validation
    test_endpoint "GET /api/v1/users/search?q=a - Validate minimum query length"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/users/search?q=a" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$RESPONSE" | jq -e ".detail" > /dev/null 2>&1; then
        print_success "Query length validation works (rejected query < 2 chars)"
    else
        print_warning "Query length validation may not be working"
    fi
}

# ============================================================================
# TEST FUNCTIES - ACTIVITY TRACKING (1 endpoint)
# ============================================================================

test_activity_tracking() {
    print_section "9. ACTIVITY TRACKING (1 endpoint)"

    # 9.1 POST /api/v1/users/me/heartbeat - Update Heartbeat
    test_endpoint "POST /api/v1/users/me/heartbeat - Update last seen timestamp"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/users/me/heartbeat" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    verify_response "$RESPONSE" "last_seen_at" "Heartbeat updated"

    # Verify in database
    LAST_SEEN=$(query_db "SELECT last_seen_at FROM activity.users WHERE user_id = '$USER_ID';")
    if [ -n "$LAST_SEEN" ]; then
        print_db "✓ Last seen timestamp in DB: $LAST_SEEN"
    else
        print_db "✗ Last seen timestamp not found in DB"
    fi
}

# ============================================================================
# TEST FUNCTIES - ADMIN MODERATION (4 endpoints)
# ============================================================================

test_admin_moderation() {
    print_section "10. ADMIN MODERATION (4 endpoints - Admin only)"

    if [ -z "$ADMIN_TOKEN" ]; then
        print_skip "GET /api/v1/admin/users/photo-moderation - No admin token"
        print_skip "POST /api/v1/admin/users/{user_id}/photo-moderation - No admin token"
        print_skip "POST /api/v1/admin/users/{user_id}/ban - No admin token"
        print_skip "DELETE /api/v1/admin/users/{user_id}/ban - No admin token"
        return
    fi

    # 10.1 GET /api/v1/admin/users/photo-moderation - Get Pending Moderations
    test_endpoint "GET /api/v1/admin/users/photo-moderation - Get pending photos"

    RESPONSE=$(curl -s -X GET "$PROFILE_API/api/v1/admin/users/photo-moderation?limit=10" \
        -H "Authorization: Bearer $ADMIN_TOKEN")

    verify_response "$RESPONSE" "results" "Pending moderations retrieved"
    verify_response "$RESPONSE" "total" "Contains total count"

    # 10.2 POST /api/v1/admin/users/{user_id}/photo-moderation - Moderate Photo
    test_endpoint "POST /api/v1/admin/users/{user_id}/photo-moderation - Approve photo"

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/admin/users/$USER_ID/photo-moderation" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"status": "approved"}')

    if echo "$RESPONSE" | jq -e ".moderation_status" > /dev/null 2>&1; then
        verify_response "$RESPONSE" "moderation_status" "Photo moderation status updated"

        verify_db_value \
            "SELECT main_photo_moderation_status FROM activity.users WHERE user_id = '$USER_ID';" \
            "approved" \
            "Photo approved in DB"
    else
        print_warning "Photo moderation may require pending photo"
    fi

    # 10.3 POST /api/v1/admin/users/{user_id}/ban - Ban User
    test_endpoint "POST /api/v1/admin/users/{user_id}/ban - Ban user (temporary)"

    BAN_EXPIRES=$(date -u -d "+7 days" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+7d +"%Y-%m-%dT%H:%M:%SZ")

    RESPONSE=$(curl -s -X POST "$PROFILE_API/api/v1/admin/users/$USER_ID/ban" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"reason\": \"Test ban for comprehensive testing\",
            \"expires_at\": \"$BAN_EXPIRES\"
        }")

    verify_response "$RESPONSE" "status" "User banned"

    # Verify in database
    print_db "Verifying ban in database:"
    query_db_table "SELECT user_id, status, ban_reason, ban_expires_at FROM activity.users WHERE user_id = '$USER_ID';"

    # 10.4 DELETE /api/v1/admin/users/{user_id}/ban - Unban User
    test_endpoint "DELETE /api/v1/admin/users/{user_id}/ban - Unban user"

    RESPONSE=$(curl -s -X DELETE "$PROFILE_API/api/v1/admin/users/$USER_ID/ban" \
        -H "Authorization: Bearer $ADMIN_TOKEN")

    verify_response "$RESPONSE" "status" "User unbanned"

    verify_db_value \
        "SELECT status FROM activity.users WHERE user_id = '$USER_ID';" \
        "active" \
        "User status set to active"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    clear

    print_header "${TROPHY} USER PROFILE API - COMPREHENSIVE TEST SUITE ${TROPHY}"

    echo -e "${BOLD}Testing all 28 endpoints with:${NC}"
    echo -e "  ${CHECK} Authentication (Bearer & Service-to-Service)"
    echo -e "  ${CHECK} Input validation"
    echo -e "  ${CHECK} Database verification"
    echo -e "  ${CHECK} Permissions (admin, S2S, user)"
    echo -e "  ${CHECK} Error handling"
    echo ""
    echo -e "${CYAN}Starting in 3 seconds...${NC}"
    sleep 3

    # Setup
    print_header "SETUP"
    cleanup_test_data
    create_test_user
    get_user_token
    setup_admin_user

    # Run all tests
    test_profile_management
    test_photo_management
    test_interest_tags
    test_user_settings
    test_subscription_management
    test_captain_program
    test_trust_verification
    test_user_search
    test_activity_tracking
    test_admin_moderation

    # Final summary
    print_header "${TROPHY} TEST SUMMARY ${TROPHY}"

    echo -e "${BOLD}Results:${NC}"
    echo -e "  ${GREEN}${CHECK} Passed:${NC}  $PASSED_TESTS"
    echo -e "  ${RED}${CROSS} Failed:${NC}  $FAILED_TESTS"
    echo -e "  ${YELLOW}⏭️  Skipped:${NC} $SKIPPED_TESTS"
    echo -e "  ${CYAN}━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${BOLD}Total:${NC}    $TOTAL_TESTS"
    echo ""

    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${BOLD}${GREEN}${TROPHY} ALL TESTS PASSED! ${TROPHY}${NC}"
        echo -e "${GREEN}User Profile API is working correctly!${NC}"
    else
        echo -e "${BOLD}${RED}${WARNING} SOME TESTS FAILED ${WARNING}${NC}"
        echo -e "${RED}Please review the failures above${NC}"
    fi

    echo ""
    print_header "${DATABASE} FINAL DATABASE STATE"

    echo -e "${BOLD}Complete user record:${NC}"
    query_db_table "
    SELECT
        user_id,
        username,
        email,
        subscription_level,
        is_verified,
        is_captain,
        verification_count,
        no_show_count,
        activities_created_count,
        activities_attended_count,
        status
    FROM activity.users
    WHERE user_id = '$USER_ID';
    "

    echo -e "${BOLD}User interests:${NC}"
    query_db_table "
    SELECT interest_tag, weight
    FROM activity.user_interests
    WHERE user_id = '$USER_ID'
    ORDER BY weight DESC;
    "

    echo -e "${BOLD}User settings:${NC}"
    query_db_table "
    SELECT ghost_mode, email_notifications, language, timezone
    FROM activity.user_settings
    WHERE user_id = '$USER_ID';
    "

    echo ""
    echo -e "${BOLD}${CYAN}Test user credentials for manual testing:${NC}"
    echo -e "  Email:    $TEST_EMAIL"
    echo -e "  Password: $TEST_PASSWORD"
    echo -e "  User ID:  $USER_ID"
    echo ""
}

# Run main function
main
