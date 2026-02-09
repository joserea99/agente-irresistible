import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://yuovxnpoolxwucsdvcsn.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl1b3Z4bnBvb2x4d3Vjc2R2Y3NuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NTc1OTQsImV4cCI6MjA4NjAzMzU5NH0._OYFzEnE3s9PgUPn18TR4ILnxd19_XurmCzmbr5YdBE';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
