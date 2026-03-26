"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";

export default function KnowledgePage() {
    const { user } = useAuthStore();
    const router = useRouter();

    useEffect(() => {
        if (user?.role === 'admin') {
            router.replace('/admin');
        } else {
            router.replace('/dashboard');
        }
    }, [user, router]);

    return null;
}
