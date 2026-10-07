-- ============================================================
-- CRJ Fastigheter AB — Supabase Schema
-- Run this SQL in the Supabase SQL editor (Dashboard > SQL Editor)
-- ============================================================

-- ---- Profiles table ----
CREATE TABLE profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  phone TEXT,
  is_tenant BOOLEAN DEFAULT FALSE,
  apartment TEXT,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---- Housing queue (legacy, kept for backwards compat) ----
CREATE TABLE housing_queue (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE SET NULL,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  preferred_size TEXT,
  move_date TEXT,
  notes TEXT,
  status TEXT DEFAULT 'pending',
  admin_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---- Queue entries (per-property queue system) ----
CREATE TABLE queue_entries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  property_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users ON DELETE SET NULL,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  preferred_size TEXT,
  notes TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','contacted','approved','rejected','withdrawn')),
  admin_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(property_id, email)
);

-- ---- Fault reports ----
CREATE TABLE fault_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE SET NULL,
  reporter_name TEXT NOT NULL,
  apartment TEXT NOT NULL,
  phone TEXT NOT NULL,
  urgency TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT DEFAULT 'open',
  admin_notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---- Contact messages ----
CREATE TABLE contact_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE SET NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  subject TEXT,
  message TEXT NOT NULL,
  status TEXT DEFAULT 'unread',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Row Level Security
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE housing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE queue_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE fault_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_messages ENABLE ROW LEVEL SECURITY;

-- ---- Profiles policies ----
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- ---- Housing queue policies ----
CREATE POLICY "Anyone can submit to housing queue" ON housing_queue
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users see own queue entry" ON housing_queue
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- ---- Queue entries policies ----
CREATE POLICY "Anyone can join queue" ON queue_entries
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Anyone can view queue count" ON queue_entries
  FOR SELECT USING (true);

CREATE POLICY "Users see own queue entry" ON queue_entries
  FOR UPDATE USING (auth.uid() = user_id);

-- ---- Fault report policies ----
CREATE POLICY "Anyone can submit fault report" ON fault_reports
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users see own fault reports" ON fault_reports
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- ---- Contact message policies ----
CREATE POLICY "Anyone can send contact message" ON contact_messages
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users see own messages" ON contact_messages
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- ============================================================
-- Admin policies (admin can see/edit all rows)
-- ============================================================
CREATE POLICY "Admin manages all queue_entries" ON queue_entries
  FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
  );

CREATE POLICY "Admin sees all queue" ON housing_queue
  FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
  );

CREATE POLICY "Admin sees all faults" ON fault_reports
  FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
  );

CREATE POLICY "Admin sees all messages" ON contact_messages
  FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
  );

CREATE POLICY "Admin sees all profiles" ON profiles
  FOR ALL USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)
  );

-- ============================================================
-- Auto-create profile on signup trigger
-- ============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- IMPORTANT: After the admin user (crjfastighet@gmail.com)
-- registers on the site, run this query to grant admin access:
--
-- UPDATE profiles SET is_admin = true WHERE email = 'crjfastighet@gmail.com';
--
-- ============================================================
