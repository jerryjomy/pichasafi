-- PichaSafi Database Schema
-- Run this in the Supabase SQL Editor to set up the database.

-- Users table
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    business_name VARCHAR(255),
    tagline VARCHAR(500),
    location VARCHAR(255),
    contact_phone VARCHAR(20),
    contact_whatsapp VARCHAR(20),
    brand_color_primary VARCHAR(7) DEFAULT '#FF6B00',
    brand_color_secondary VARCHAR(7) DEFAULT '#FFFFFF',
    brand_color_bg VARCHAR(7) DEFAULT '#1A1A2E',
    template_style VARCHAR(50) DEFAULT 'modern',
    logo_url TEXT,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    images_created_this_month INTEGER DEFAULT 0,
    monthly_limit INTEGER DEFAULT 3,
    onboarding_step VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_phone ON users(phone_number);

-- Generated images table
CREATE TABLE generated_images (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    image_type VARCHAR(50) NOT NULL,
    template_used VARCHAR(100),
    original_image_url TEXT,
    result_image_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_images_user ON generated_images(user_id);

-- Transactions table (for Phase 3, created now for schema completeness)
CREATE TABLE transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    transaction_ref VARCHAR(255),
    transaction_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at on users table
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
