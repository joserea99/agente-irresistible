import {
    Brain,
    Library,
    Zap,
    MessageSquare,
    Download,
    CheckCircle,
    Users,
    Video,
    Music,
    Heart,
    Calendar,
    Megaphone,
    BookOpen,
    Smile
} from "lucide-react";

export type QuickAction = {
    title: string;
    desc: string;
    icon: any; // Lucide icon component
    href: string;
    color: string;
};

export type StatCard = {
    label: string;
    value: string;
    icon: any;
    color: string;
    desc: string;
};

export type DashboardConfig = {
    greeting: (name: string) => string;
    stats: StatCard[];
    quickActions: QuickAction[];
};

// ============================================================================
// ROLE CONFIGURATIONS
// ============================================================================

const DEFAULT_CONFIG: DashboardConfig = {
    greeting: (name) => `Welcome back, ${name}`,
    stats: [
        { label: "Active Session", value: "Online", icon: Brain, color: "text-purple-500", desc: "System ready" },
        { label: "Knowledge Base", value: "Indexed", icon: Library, color: "text-blue-500", desc: "Search enabled" },
        { label: "System Status", value: "98%", icon: Zap, color: "text-green-500", desc: "Operational" },
    ],
    quickActions: [
        {
            title: "New Session",
            desc: "Start a new chat",
            icon: MessageSquare,
            href: "/chat",
            color: "bg-primary/10 text-primary border-primary/20",
        },
        {
            title: "Ingest Data",
            desc: "Add to knowledge base",
            icon: Download,
            href: "/knowledge",
            color: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        },
        {
            title: "Settings",
            desc: "Manage account",
            icon: CheckCircle,
            href: "/settings",
            color: "bg-slate-500/10 text-slate-500 border-slate-500/20",
        },
    ],
};

const PASTOR_CONFIG: DashboardConfig = {
    greeting: (name) => `Ready to lead, Pastor ${name}?`,
    stats: [
        { label: "Sermon Series", value: "Upcoming", icon: BookOpen, color: "text-purple-500", desc: "Preparation Mode" },
        { label: "Leadership", value: "6 Directors", icon: Users, color: "text-blue-500", desc: "Team Alignment" },
        { label: "Vision", value: "On Track", icon: Zap, color: "text-yellow-500", desc: "Strategic Goals" },
    ],
    quickActions: [
        {
            title: "Sermon Prep",
            desc: "Research & Illustrations",
            icon: BookOpen,
            href: "/chat?director=pastor_principal&mode=prep",
            color: "bg-purple-500/10 text-purple-500 border-purple-500/20",
        },
        {
            title: "Staff Meeting",
            desc: "Generate Agenda",
            icon: Users,
            href: "/chat?director=pastor_principal&mode=staff",
            color: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        },
        {
            title: "Strategic Planning",
            desc: "Vision & Goals",
            icon: Brain,
            href: "/chat?director=pastor_principal&mode=strategy",
            color: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
        },
    ],
};

const KIDS_DIRECTOR_CONFIG: DashboardConfig = {
    greeting: (name) => `Let's impact the next generation, ${name}!`,
    stats: [
        { label: "This Sunday", value: "Ready", icon: Calendar, color: "text-green-500", desc: "Curriculum Checked" },
        { label: "Volunteers", value: "Active", icon: Heart, color: "text-red-500", desc: "Team Health" },
        { label: "Parents", value: "Engaged", icon: Smile, color: "text-yellow-500", desc: "Communication" },
    ],
    quickActions: [
        {
            title: "Curriculum",
            desc: "Review this week's lesson",
            icon: BookOpen,
            href: "/chat?director=kids_director&mode=curriculum",
            color: "bg-orange-500/10 text-orange-500 border-orange-500/20",
        },
        {
            title: "Parent Emails",
            desc: "Draft weekly update",
            icon: MessageSquare,
            href: "/chat?director=kids_director&mode=parents",
            color: "bg-green-500/10 text-green-500 border-green-500/20",
        },
        {
            title: "Angry Parent Sim",
            desc: "Practice conflict resolution",
            icon: Zap,
            href: "/dojo",
            color: "bg-red-500/10 text-red-500 border-red-500/20",
        },
    ],
};

const MEDIA_DIRECTOR_CONFIG: DashboardConfig = {
    greeting: (name) => `What are we creating today, ${name}?`,
    stats: [
        { label: "Brand Assets", value: "Indexed", icon: Library, color: "text-pink-500", desc: "Brandfolder Connected" },
        { label: "Social Reach", value: "Growing", icon: Megaphone, color: "text-blue-500", desc: "Engagement Up" },
        { label: "Production", value: "Stable", icon: Video, color: "text-green-500", desc: "System Check" },
    ],
    quickActions: [
        {
            title: "Asset Search",
            desc: "Find B-Roll & Graphics",
            icon: Library,
            href: "/chat?director=media_director&mode=search",
            color: "bg-pink-500/10 text-pink-500 border-pink-500/20",
        },
        {
            title: "Social Copy",
            desc: "Generate captions",
            icon: Megaphone,
            href: "/chat?director=media_director&mode=social",
            color: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        },
        {
            title: "Production Plan",
            desc: "Run sheet assistance",
            icon: Video,
            href: "/chat?director=service_director", // Media works closely with Service Programming
            color: "bg-purple-500/10 text-purple-500 border-purple-500/20",
        },
    ],
};

// ============================================================================
// CONFIG EXPORT
// ============================================================================

export const ROLE_CONFIGS: Record<string, DashboardConfig> = {
    "admin": DEFAULT_CONFIG,
    "member": DEFAULT_CONFIG,
    "pastor_principal": PASTOR_CONFIG,
    "lead_pastor": PASTOR_CONFIG, // Alias
    "kids_director": KIDS_DIRECTOR_CONFIG,
    "media_director": MEDIA_DIRECTOR_CONFIG,
    "editorial_director": MEDIA_DIRECTOR_CONFIG, // Alias or similar
    "service_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Let's design an experience, ${name}.`,
        quickActions: [
            {
                title: "Run Sheet",
                desc: "Plan the service flow",
                icon: Calendar,
                href: "/chat?director=service_director&mode=runsheet",
                color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
            },
            ...DEFAULT_CONFIG.quickActions.slice(1)
        ]
    },
    // New Roles (using default config for now)
    "students_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Ready for NextGen (Students), ${name}?`
    },
    "adults_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Let's connect people, ${name}.`
    },
    "operations_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Systems check, ${name}.`
    },
    "guest_services_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Welcome the guests, ${name}!`
    },
    "philosophy_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Clarify the win, ${name}.`
    },
    "be_rich_director": {
        ...DEFAULT_CONFIG,
        greeting: (name) => `Give, Serve, Love, ${name}.`
    }
};

export const getDashboardConfig = (role: string = "member"): DashboardConfig => {
    return ROLE_CONFIGS[role] || DEFAULT_CONFIG;
};
