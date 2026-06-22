import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createServerClient } from '@supabase/ssr';

export async function proxy(request: NextRequest) {
    const response = NextResponse.next({
        request: { headers: request.headers },
    });

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://yuovxnpoolxwucsdvcsn.supabase.co';
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl1b3Z4bnBvb2x4d3Vjc2R2Y3NuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NTc1OTQsImV4cCI6MjA4NjAzMzU5NH0._OYFzEnE3s9PgUPn18TR4ILnxd19_XurmCzmbr5YdBE';

    const protectedRoutes = ['/dashboard', '/chat', '/dojo', '/knowledge', '/subscription', '/admin'];
    const isProtectedRoute = protectedRoutes.some(route =>
        request.nextUrl.pathname.startsWith(route)
    );

    try {
        // Build a Supabase client that reads/writes cookies from the request.
        const supabase = createServerClient(
            supabaseUrl,
            supabaseAnonKey,
            {
                cookies: {
                    getAll() {
                        return request.cookies.getAll();
                    },
                    setAll(cookiesToSet) {
                        cookiesToSet.forEach(({ name, value, options }) => {
                            request.cookies.set(name, value);
                            response.cookies.set(name, value, options);
                        });
                    },
                },
            }
        );

        // Refresh the session (this also rotates the cookie if needed).
        const { data: { user } } = await supabase.auth.getUser();

        if (isProtectedRoute && !user) {
            const loginUrl = new URL('/login', request.url);
            loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
            return NextResponse.redirect(loginUrl);
        }
    } catch (error) {
        // If anything fails (e.g., missing env vars, supabase down), redirect protected routes to login instead of 500
        console.error("Middleware Auth Error:", error);
        if (isProtectedRoute) {
            const loginUrl = new URL('/login', request.url);
            loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
            return NextResponse.redirect(loginUrl);
        }
    }

    return response;
}

export const config = {
    matcher: [
        '/dashboard/:path*',
        '/chat/:path*',
        '/dojo/:path*',
        '/knowledge/:path*',
        '/subscription/:path*',
        '/admin/:path*',
    ],
};
