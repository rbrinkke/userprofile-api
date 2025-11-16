-- ============================================================================
-- USER PROFILE API STORED PROCEDURES
-- Complete implementation of all 23 stored procedures
-- Database: PostgreSQL | Schema: activity
-- ============================================================================

-- ============================================================================
-- 1. sp_get_user_profile
-- Purpose: Retrieve complete user profile with interests and settings
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_get_user_profile(
    p_user_id UUID,
    p_requesting_user_id UUID
)
RETURNS TABLE (
    user_id UUID,
    email VARCHAR(255),
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_description TEXT,
    main_photo_url VARCHAR(500),
    main_photo_moderation_status activity.photo_moderation_status,
    profile_photos_extra JSONB,
    date_of_birth DATE,
    gender VARCHAR(50),
    subscription_level activity.subscription_level,
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    is_captain BOOLEAN,
    captain_since TIMESTAMP WITH TIME ZONE,
    is_verified BOOLEAN,
    verification_count INT,
    no_show_count INT,
    activities_created_count INT,
    activities_attended_count INT,
    created_at TIMESTAMP WITH TIME ZONE,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    interests JSONB,
    settings JSONB
) AS $$
BEGIN
    -- Check if requesting user has blocked the target user
    IF EXISTS (
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_requesting_user_id
        AND blocked_user_id = p_user_id
    ) THEN
        RETURN;  -- Return NULL (blocked)
    END IF;

    -- Check if target user has blocked the requesting user
    IF EXISTS (
        SELECT 1 FROM activity.user_blocks
        WHERE blocker_user_id = p_user_id
        AND blocked_user_id = p_requesting_user_id
    ) THEN
        RETURN;  -- Return NULL (blocking)
    END IF;

    -- Return complete profile with aggregated interests and settings
    RETURN QUERY
    SELECT
        u.user_id,
        u.email,
        u.username,
        u.first_name,
        u.last_name,
        u.profile_description,
        u.main_photo_url,
        u.main_photo_moderation_status,
        u.profile_photos_extra,
        u.date_of_birth,
        u.gender,
        u.subscription_level,
        u.subscription_expires_at,
        u.is_captain,
        u.captain_since,
        u.is_verified,
        u.verification_count,
        u.no_show_count,
        u.activities_created_count,
        u.activities_attended_count,
        u.created_at,
        u.last_seen_at,
        COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object('tag', ui.interest_tag, 'weight', ui.weight))
                FROM activity.user_interests ui
                WHERE ui.user_id = p_user_id
            ),
            '[]'::jsonb
        ) AS interests,
        COALESCE(
            (
                SELECT to_jsonb(us.*) - 'user_id' - 'created_at' - 'updated_at' - 'payload' - 'hash_value'
                FROM activity.user_settings us
                WHERE us.user_id = p_user_id
            ),
            '{}'::jsonb
        ) AS settings
    FROM activity.users u
    WHERE u.user_id = p_user_id
    AND u.status != 'banned';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 2. sp_update_user_profile
-- Purpose: Update user profile fields (name, description, dob, gender)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_update_user_profile(
    p_user_id UUID,
    p_first_name VARCHAR(100) DEFAULT NULL,
    p_last_name VARCHAR(100) DEFAULT NULL,
    p_profile_description TEXT DEFAULT NULL,
    p_date_of_birth DATE DEFAULT NULL,
    p_gender VARCHAR(50) DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    v_user_status activity.user_status;
BEGIN
    -- Check user exists and get status
    SELECT status INTO v_user_status
    FROM activity.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::TIMESTAMP WITH TIME ZONE;
        RETURN;
    END IF;

    -- Check user is not banned
    IF v_user_status = 'banned' THEN
        RAISE EXCEPTION 'User is banned and cannot update profile';
    END IF;

    -- Validate date_of_birth (must not be in future, must be 18+ years old)
    IF p_date_of_birth IS NOT NULL THEN
        IF p_date_of_birth >= CURRENT_DATE THEN
            RAISE EXCEPTION 'Date of birth cannot be in the future';
        END IF;
        IF p_date_of_birth > CURRENT_DATE - INTERVAL '18 years' THEN
            RAISE EXCEPTION 'User must be at least 18 years old';
        END IF;
    END IF;

    -- Update only non-NULL fields
    UPDATE activity.users
    SET
        first_name = COALESCE(p_first_name, first_name),
        last_name = COALESCE(p_last_name, last_name),
        profile_description = COALESCE(p_profile_description, profile_description),
        date_of_birth = COALESCE(p_date_of_birth, date_of_birth),
        gender = COALESCE(p_gender, gender),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE, NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. sp_update_username
-- Purpose: Change username (must be unique)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_update_username(
    p_user_id UUID,
    p_new_username VARCHAR(100)
)
RETURNS TABLE (
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_username_exists BOOLEAN;
BEGIN
    -- Validate username format (alphanumeric + underscore, 3-30 chars)
    IF NOT p_new_username ~ '^[a-zA-Z0-9_]{3,30}$' THEN
        RAISE EXCEPTION 'Username must be 3-30 characters and contain only letters, numbers, and underscores';
    END IF;

    -- Check uniqueness (case insensitive)
    SELECT EXISTS (
        SELECT 1 FROM activity.users
        WHERE LOWER(username) = LOWER(p_new_username)
        AND user_id != p_user_id
    ) INTO v_username_exists;

    IF v_username_exists THEN
        RETURN QUERY SELECT FALSE, 'Username already taken'::TEXT;
        RETURN;
    END IF;

    -- Update username
    UPDATE activity.users
    SET username = p_new_username, updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'User not found'::TEXT;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'Username updated successfully'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. sp_set_main_photo
-- Purpose: Set main profile photo (triggers moderation)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_set_main_photo(
    p_user_id UUID,
    p_photo_url VARCHAR(500)
)
RETURNS TABLE (
    success BOOLEAN,
    moderation_status activity.photo_moderation_status
) AS $$
BEGIN
    -- Validate URL format
    IF p_photo_url !~ '^https?://' THEN
        RAISE EXCEPTION 'Photo URL must be a valid HTTP/HTTPS URL';
    END IF;

    -- Update main photo and set moderation status to pending
    UPDATE activity.users
    SET
        main_photo_url = p_photo_url,
        main_photo_moderation_status = 'pending',
        updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::activity.photo_moderation_status;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'pending'::activity.photo_moderation_status;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. sp_add_profile_photo
-- Purpose: Add photo to extra photos array (max 8 total)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_add_profile_photo(
    p_user_id UUID,
    p_photo_url VARCHAR(500)
)
RETURNS TABLE (
    success BOOLEAN,
    message TEXT,
    photo_count INT
) AS $$
DECLARE
    v_current_photos JSONB;
    v_photo_count INT;
BEGIN
    -- Get current photos
    SELECT profile_photos_extra INTO v_current_photos
    FROM activity.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'User not found'::TEXT, 0;
        RETURN;
    END IF;

    -- Check photo count
    v_photo_count := jsonb_array_length(v_current_photos);

    IF v_photo_count >= 8 THEN
        RETURN QUERY SELECT FALSE, 'Maximum 8 photos allowed'::TEXT, v_photo_count;
        RETURN;
    END IF;

    -- Check if photo already exists
    IF v_current_photos @> to_jsonb(ARRAY[p_photo_url]) THEN
        RETURN QUERY SELECT FALSE, 'Photo already added'::TEXT, v_photo_count;
        RETURN;
    END IF;

    -- Add photo to array
    UPDATE activity.users
    SET
        profile_photos_extra = profile_photos_extra || to_jsonb(ARRAY[p_photo_url]),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE, 'Photo added successfully'::TEXT, v_photo_count + 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. sp_remove_profile_photo
-- Purpose: Remove photo from extra photos array
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_remove_profile_photo(
    p_user_id UUID,
    p_photo_url VARCHAR(500)
)
RETURNS TABLE (
    success BOOLEAN,
    photo_count INT
) AS $$
DECLARE
    v_current_photos JSONB;
    v_new_photos JSONB;
    v_photo_count INT;
BEGIN
    -- Get current photos
    SELECT profile_photos_extra INTO v_current_photos
    FROM activity.users
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 0;
        RETURN;
    END IF;

    -- Remove photo from array
    SELECT jsonb_agg(elem)
    INTO v_new_photos
    FROM jsonb_array_elements_text(v_current_photos) elem
    WHERE elem != p_photo_url;

    -- Handle case where all photos were removed
    v_new_photos := COALESCE(v_new_photos, '[]'::jsonb);
    v_photo_count := jsonb_array_length(v_new_photos);

    -- Update photos
    UPDATE activity.users
    SET
        profile_photos_extra = v_new_photos,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE, v_photo_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. sp_set_user_interests
-- Purpose: Set complete interest tags list (replaces existing)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_set_user_interests(
    p_user_id UUID,
    p_interests JSONB
)
RETURNS TABLE (
    success BOOLEAN,
    interest_count INT
) AS $$
DECLARE
    v_interest_count INT;
    v_interest JSONB;
BEGIN
    -- Validate JSONB structure and count
    IF jsonb_typeof(p_interests) != 'array' THEN
        RAISE EXCEPTION 'Interests must be a JSON array';
    END IF;

    v_interest_count := jsonb_array_length(p_interests);

    IF v_interest_count > 20 THEN
        RETURN QUERY SELECT FALSE, v_interest_count;
        RETURN;
    END IF;

    -- Validate each interest object
    FOR v_interest IN SELECT * FROM jsonb_array_elements(p_interests)
    LOOP
        IF NOT (v_interest ? 'tag' AND v_interest ? 'weight') THEN
            RAISE EXCEPTION 'Each interest must have tag and weight fields';
        END IF;

        IF (v_interest->>'weight')::DECIMAL < 0 OR (v_interest->>'weight')::DECIMAL > 1 THEN
            RAISE EXCEPTION 'Interest weight must be between 0.0 and 1.0';
        END IF;
    END LOOP;

    -- Delete existing interests
    DELETE FROM activity.user_interests
    WHERE user_id = p_user_id;

    -- Insert new interests
    INSERT INTO activity.user_interests (user_id, interest_tag, weight)
    SELECT
        p_user_id,
        interest->>'tag',
        (interest->>'weight')::DECIMAL
    FROM jsonb_array_elements(p_interests) AS interest;

    RETURN QUERY SELECT TRUE, v_interest_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. sp_add_user_interest
-- Purpose: Add single interest tag
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_add_user_interest(
    p_user_id UUID,
    p_interest_tag VARCHAR(100),
    p_weight DECIMAL(3,2) DEFAULT 1.0
)
RETURNS TABLE (
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_interest_count INT;
BEGIN
    -- Validate weight
    IF p_weight < 0 OR p_weight > 1 THEN
        RAISE EXCEPTION 'Interest weight must be between 0.0 and 1.0';
    END IF;

    -- Count existing interests
    SELECT COUNT(*) INTO v_interest_count
    FROM activity.user_interests
    WHERE user_id = p_user_id;

    IF v_interest_count >= 20 THEN
        RETURN QUERY SELECT FALSE, 'Maximum 20 interests allowed'::TEXT;
        RETURN;
    END IF;

    -- Insert or update interest
    INSERT INTO activity.user_interests (user_id, interest_tag, weight)
    VALUES (p_user_id, p_interest_tag, p_weight)
    ON CONFLICT (user_id, interest_tag)
    DO UPDATE SET weight = p_weight, updated_at = NOW();

    RETURN QUERY SELECT TRUE, 'Interest added successfully'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 9. sp_remove_user_interest
-- Purpose: Remove single interest tag
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_remove_user_interest(
    p_user_id UUID,
    p_interest_tag VARCHAR(100)
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    DELETE FROM activity.user_interests
    WHERE user_id = p_user_id
    AND interest_tag = p_interest_tag;

    RETURN QUERY SELECT TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 10. sp_get_user_settings
-- Purpose: Retrieve user settings (creates defaults if not exists)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_get_user_settings(
    p_user_id UUID
)
RETURNS TABLE (
    email_notifications BOOLEAN,
    push_notifications BOOLEAN,
    activity_reminders BOOLEAN,
    community_updates BOOLEAN,
    friend_requests BOOLEAN,
    marketing_emails BOOLEAN,
    ghost_mode BOOLEAN,
    language VARCHAR(10),
    timezone VARCHAR(50)
) AS $$
BEGIN
    -- Create default settings if not exists
    INSERT INTO activity.user_settings (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    -- Return settings
    RETURN QUERY
    SELECT
        us.email_notifications,
        us.push_notifications,
        us.activity_reminders,
        us.community_updates,
        us.friend_requests,
        us.marketing_emails,
        us.ghost_mode,
        us.language,
        us.timezone
    FROM activity.user_settings us
    WHERE us.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 11. sp_update_user_settings
-- Purpose: Update user settings (partial update)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_update_user_settings(
    p_user_id UUID,
    p_email_notifications BOOLEAN DEFAULT NULL,
    p_push_notifications BOOLEAN DEFAULT NULL,
    p_activity_reminders BOOLEAN DEFAULT NULL,
    p_community_updates BOOLEAN DEFAULT NULL,
    p_friend_requests BOOLEAN DEFAULT NULL,
    p_marketing_emails BOOLEAN DEFAULT NULL,
    p_ghost_mode BOOLEAN DEFAULT NULL,
    p_language VARCHAR(10) DEFAULT NULL,
    p_timezone VARCHAR(50) DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
DECLARE
    v_subscription_level activity.subscription_level;
BEGIN
    -- Create settings if not exists
    INSERT INTO activity.user_settings (user_id)
    VALUES (p_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    -- Check subscription level for ghost_mode
    IF p_ghost_mode = TRUE THEN
        SELECT subscription_level INTO v_subscription_level
        FROM activity.users
        WHERE user_id = p_user_id;

        IF v_subscription_level != 'premium' THEN
            RAISE EXCEPTION 'Ghost mode requires Premium subscription';
        END IF;
    END IF;

    -- Update only non-NULL fields
    UPDATE activity.user_settings
    SET
        email_notifications = COALESCE(p_email_notifications, email_notifications),
        push_notifications = COALESCE(p_push_notifications, push_notifications),
        activity_reminders = COALESCE(p_activity_reminders, activity_reminders),
        community_updates = COALESCE(p_community_updates, community_updates),
        friend_requests = COALESCE(p_friend_requests, friend_requests),
        marketing_emails = COALESCE(p_marketing_emails, marketing_emails),
        ghost_mode = COALESCE(p_ghost_mode, ghost_mode),
        language = COALESCE(p_language, language),
        timezone = COALESCE(p_timezone, timezone),
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 12. sp_update_subscription
-- Purpose: Update user subscription level
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_update_subscription(
    p_user_id UUID,
    p_subscription_level activity.subscription_level,
    p_subscription_expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    -- Validate: free requires NULL expiry, club/premium require expiry
    IF p_subscription_level = 'free' AND p_subscription_expires_at IS NOT NULL THEN
        RAISE EXCEPTION 'Free subscription cannot have expiry date';
    END IF;

    IF p_subscription_level IN ('club', 'premium') AND p_subscription_expires_at IS NULL THEN
        RAISE EXCEPTION 'Club and Premium subscriptions must have expiry date';
    END IF;

    -- Update subscription
    UPDATE activity.users
    SET
        subscription_level = p_subscription_level,
        subscription_expires_at = p_subscription_expires_at,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    -- If downgrading from premium, disable ghost_mode
    IF p_subscription_level != 'premium' THEN
        UPDATE activity.user_settings
        SET ghost_mode = FALSE, updated_at = NOW()
        WHERE user_id = p_user_id AND ghost_mode = TRUE;
    END IF;

    RETURN QUERY SELECT TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 13. sp_set_captain_status
-- Purpose: Grant/revoke Captain program membership
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_set_captain_status(
    p_user_id UUID,
    p_is_captain BOOLEAN
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    IF p_is_captain = TRUE THEN
        -- Grant captain status
        UPDATE activity.users
        SET
            is_captain = TRUE,
            captain_since = NOW(),
            subscription_level = 'premium',
            subscription_expires_at = NOW() + INTERVAL '1 year',
            updated_at = NOW()
        WHERE user_id = p_user_id;
    ELSE
        -- Revoke captain status
        UPDATE activity.users
        SET
            is_captain = FALSE,
            captain_since = NULL,
            subscription_level = 'free',
            subscription_expires_at = NULL,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    END IF;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 14. sp_increment_verification_count
-- Purpose: Increment verification count (called after peer verification)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_increment_verification_count(
    p_user_id UUID
)
RETURNS TABLE (
    new_count INT
) AS $$
DECLARE
    v_new_count INT;
BEGIN
    UPDATE activity.users
    SET
        verification_count = verification_count + 1,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING verification_count INTO v_new_count;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    RETURN QUERY SELECT v_new_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 15. sp_increment_no_show_count
-- Purpose: Increment no-show count (called after no-show report)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_increment_no_show_count(
    p_user_id UUID
)
RETURNS TABLE (
    new_count INT
) AS $$
DECLARE
    v_new_count INT;
BEGIN
    UPDATE activity.users
    SET
        no_show_count = no_show_count + 1,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING no_show_count INTO v_new_count;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    RETURN QUERY SELECT v_new_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 16. sp_update_activity_counts
-- Purpose: Update activity counters
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_update_activity_counts(
    p_user_id UUID,
    p_created_delta INT,
    p_attended_delta INT
)
RETURNS TABLE (
    new_created_count INT,
    new_attended_count INT
) AS $$
DECLARE
    v_new_created INT;
    v_new_attended INT;
BEGIN
    UPDATE activity.users
    SET
        activities_created_count = GREATEST(0, activities_created_count + p_created_delta),
        activities_attended_count = GREATEST(0, activities_attended_count + p_attended_delta),
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING activities_created_count, activities_attended_count
    INTO v_new_created, v_new_attended;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User not found';
    END IF;

    -- Verify counts didn't go negative
    IF v_new_created < 0 OR v_new_attended < 0 THEN
        RAISE EXCEPTION 'Activity counts cannot be negative';
    END IF;

    RETURN QUERY SELECT v_new_created, v_new_attended;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 17. sp_update_last_seen
-- Purpose: Update last seen timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_update_last_seen(
    p_user_id UUID
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    UPDATE activity.users
    SET last_seen_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 18. sp_search_users
-- Purpose: Search users by name or username
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_search_users(
    p_query TEXT,
    p_requesting_user_id UUID,
    p_limit INT DEFAULT 20,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    user_id UUID,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    main_photo_url VARCHAR(500),
    is_verified BOOLEAN,
    verification_count INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.username,
        u.first_name,
        u.last_name,
        u.main_photo_url,
        u.is_verified,
        u.verification_count
    FROM activity.users u
    WHERE
        u.status = 'active'
        AND (
            u.username ILIKE '%' || p_query || '%'
            OR u.first_name ILIKE '%' || p_query || '%'
            OR u.last_name ILIKE '%' || p_query || '%'
        )
        -- Exclude blocked users (either direction)
        AND NOT EXISTS (
            SELECT 1 FROM activity.user_blocks
            WHERE (blocker_user_id = p_requesting_user_id AND blocked_user_id = u.user_id)
            OR (blocker_user_id = u.user_id AND blocked_user_id = p_requesting_user_id)
        )
    ORDER BY u.verification_count DESC, u.username ASC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 19. sp_ban_user
-- Purpose: Ban user temporarily or permanently
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_ban_user(
    p_user_id UUID,
    p_ban_reason TEXT,
    p_ban_expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    -- Validate expiry date (must be in future if provided)
    IF p_ban_expires_at IS NOT NULL AND p_ban_expires_at <= NOW() THEN
        RAISE EXCEPTION 'Ban expiry date must be in the future';
    END IF;

    -- Update user status
    IF p_ban_expires_at IS NULL THEN
        -- Permanent ban
        UPDATE activity.users
        SET
            status = 'banned',
            ban_reason = p_ban_reason,
            ban_expires_at = NULL,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    ELSE
        -- Temporary ban
        UPDATE activity.users
        SET
            status = 'temporary_ban',
            ban_reason = p_ban_reason,
            ban_expires_at = p_ban_expires_at,
            updated_at = NOW()
        WHERE user_id = p_user_id;
    END IF;

    RETURN QUERY SELECT FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 20. sp_unban_user
-- Purpose: Remove ban from user
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_unban_user(
    p_user_id UUID
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    UPDATE activity.users
    SET
        status = 'active',
        ban_reason = NULL,
        ban_expires_at = NULL,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 21. sp_moderate_main_photo
-- Purpose: Approve or reject main photo moderation
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_moderate_main_photo(
    p_user_id UUID,
    p_moderation_status activity.photo_moderation_status,
    p_moderator_user_id UUID
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    -- Validate status
    IF p_moderation_status NOT IN ('approved', 'rejected') THEN
        RAISE EXCEPTION 'Moderation status must be approved or rejected';
    END IF;

    -- Update moderation status
    UPDATE activity.users
    SET
        main_photo_moderation_status = p_moderation_status,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    RETURN QUERY SELECT FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 22. sp_get_pending_photo_moderations
-- Purpose: Get list of users with pending main photo moderation
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_get_pending_photo_moderations(
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    user_id UUID,
    username VARCHAR(100),
    email VARCHAR(255),
    main_photo_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.user_id,
        u.username,
        u.email,
        u.main_photo_url,
        u.created_at
    FROM activity.users u
    WHERE u.main_photo_moderation_status = 'pending'
    ORDER BY u.created_at ASC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 23. sp_delete_user_account
-- Purpose: Soft delete user account (for GDPR compliance)
-- ============================================================================

CREATE OR REPLACE FUNCTION activity.sp_delete_user_account(
    p_user_id UUID
)
RETURNS TABLE (
    success BOOLEAN
) AS $$
BEGIN
    -- Anonymize user data
    UPDATE activity.users
    SET
        email = 'deleted_' || p_user_id::TEXT || '@deleted.local',
        username = 'deleted_' || p_user_id::TEXT,
        first_name = NULL,
        last_name = NULL,
        profile_description = NULL,
        main_photo_url = NULL,
        profile_photos_extra = '[]'::JSONB,
        date_of_birth = NULL,
        status = 'banned',
        updated_at = NOW()
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE;
        RETURN;
    END IF;

    -- Delete related data
    DELETE FROM activity.user_interests WHERE user_id = p_user_id;
    DELETE FROM activity.user_settings WHERE user_id = p_user_id;

    RETURN QUERY SELECT TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- END OF STORED PROCEDURES
-- ============================================================================

-- Grant execute permissions to application user
-- Note: activity_user role must be created first
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA activity TO activity_user;
