import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

// Secret key for JWT (Must match backend)
// In a real app, use process.env.SECRET_KEY
const SECRET_KEY = new TextEncoder().encode(process.env.SECRET_KEY || "supersecretkey");

export async function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token')?.value;

    // Define protected routes
    const protectedRoutes = ['/dashboard', '/chat'];
    const isProtectedRoute = protectedRoutes.some(route => request.nextUrl.pathname.startsWith(route));

    if (isProtectedRoute) {
        if (!token) {
            return NextResponse.redirect(new URL('/login', request.url));
        }

        try {
            // Verify JWT
            const { payload } = await jwtVerify(token, SECRET_KEY);

            // Check Subscription Status
            const subscriptionStatus = payload.subscription_status as string;

            if (subscriptionStatus === 'trial_expired' || subscriptionStatus === 'expired') {
                // Redirect to subscription page
                return NextResponse.redirect(new URL('/subscription?reason=trial_expired', request.url));
            }

        } catch (error) {
            console.error("Token verification failed:", error);
            // Redirect to login if token is invalid
            return NextResponse.redirect(new URL('/login', request.url));
        }
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/dashboard/:path*', '/chat/:path*', '/subscription/:path*', '/admin/:path*'],
};
