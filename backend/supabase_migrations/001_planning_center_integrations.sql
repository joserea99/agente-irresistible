-- Planning Center OAuth Integration Table
-- Run this SQL in your Supabase SQL Editor (Dashboard → SQL Editor → New Query)

CREATE TABLE IF NOT EXISTS public.planning_center_integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  access_token TEXT NOT NULL,
  refresh_token TEXT NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  church_name TEXT DEFAULT '',
  connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Enable Row Level Security
ALTER TABLE public.planning_center_integrations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see/modify their own integration
CREATE POLICY "Users manage own planning_center integration"
  ON public.planning_center_integrations
  FOR ALL
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Policy: Service role can manage all (for backend operations)
CREATE POLICY "Service role full access"
  ON public.planning_center_integrations
  FOR ALL
  USING (auth.role() = 'service_role');
