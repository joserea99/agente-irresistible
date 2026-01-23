
"use client";

import { useEffect, useState } from "react";
import { useAuthStore, api } from "@/lib/store";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

interface User {
    username: string;
    full_name: string;
    role: string;
    subscription_status: string;
    trial_start_date: string;
}

export default function AdminPage() {
    const { user } = useAuthStore();
    const router = useRouter();
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Basic protection (client-side only for now)
        if (user?.role !== "admin") {
            router.push("/dashboard");
            return;
        }

        fetchUsers();
    }, [user]);

    const fetchUsers = async () => {
        try {
            const res = await api.get("/auth/users");
            setUsers(res.data);
        } catch (err) {
            console.error("Failed to fetch users", err);
        } finally {
            setLoading(false);
        }
    };

    const deleteUser = async (username: string) => {
        if (!confirm(`Are you sure you want to delete ${username}?`)) return;
        try {
            await api.delete(`/auth/users/${username}`);
            setUsers(users.filter((u) => u.username !== username));
        } catch (err) {
            alert("Failed to delete user");
        }
    };

    if (loading) return <div className="p-8 text-white">Loading users...</div>;

    return (
        <div className="min-h-screen bg-slate-950 p-8 text-white">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold">Admin Panel</h1>
                    <Button onClick={() => router.push("/dashboard")} variant="outline">
                        Back to Dashboard
                    </Button>
                </div>

                <div className="bg-slate-900 rounded-lg p-6 shadow-xl border border-slate-800">
                    <h2 className="text-xl font-semibold mb-4">User Management</h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-700 text-slate-400">
                                    <th className="p-3">Username</th>
                                    <th className="p-3">Full Name</th>
                                    <th className="p-3">Role</th>
                                    <th className="p-3">Status</th>
                                    <th className="p-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((u) => (
                                    <tr key={u.username} className="border-b border-slate-800 hover:bg-slate-800/50">
                                        <td className="p-3">{u.username}</td>
                                        <td className="p-3">{u.full_name}</td>
                                        <td className="p-3">
                                            <span className={`px-2 py-1 rounded text-xs ${u.role === 'admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                                                {u.role}
                                            </span>
                                        </td>
                                        <td className="p-3">
                                            <span className={`text-xs ${u.subscription_status === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
                                                {u.subscription_status}
                                            </span>
                                        </td>
                                        <td className="p-3">
                                            {u.role !== "admin" && (
                                                <Button
                                                    variant="destructive"
                                                    size="sm"
                                                    onClick={() => deleteUser(u.username)}
                                                >
                                                    Delete
                                                </Button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
