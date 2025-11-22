-- Enable PostGIS extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add location column to activity.users
ALTER TABLE activity.users
ADD COLUMN location GEOGRAPHY(POINT, 4326);

-- Create GiST index on the new location column
CREATE INDEX idx_users_location ON activity.users USING GIST (location);
