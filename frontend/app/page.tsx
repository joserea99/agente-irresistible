"use client";

import { useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/lib/store";
import {
    BookOpen,
    Users,
    Heart,
    Clock,
    Share2,
    Sparkles,
    ArrowRight,
    CheckCircle2,
    Library,
    Swords,
    ShieldCheck,
} from "lucide-react";

const SAMPLE_DELIVERABLES = {
    sermon: {
        title: "1. Bosquejo de Predicación (Mapa de 5 Movimientos)",
        badge: "Estructura Narrativa",
        preview: `### Título: Cómo no ser tu peor enemigo
**Frase Memorable (Big Idea):** *Nuestras decisiones de hoy escriben las historias que contaremos mañana.*

#### 1. YO (Me) — Tensión Personal (5 min)
Todos hemos mirado atrás alguna vez diciendo: "¿En qué estaba pensando cuando compré eso, dije eso o empecé esa relación?". El mayor saboteador de nuestra paz rara vez está afuera; nos mira desde el espejo.

#### 2. NOSOTROS (We) — Tensión Común (5 min)
En nuestra cultura tomamos decisiones preguntando: *"¿Tiene algo de malo?"* (rozando el límite). Pero vivir al límite nos deja sin margen moral, financiero ni familiar.

#### 3. DIOS (God) — La Verdad Bíblica (15 min)
**Efesios 5:15-17:** *"Mirad, pues, con diligencia cómo andéis, no como necios sino como sabios, aprovechando bien el tiempo..."*
Pablo nos propone cambiar la pregunta de *"¿Es pecado?"* a **"¿Qué es lo más sabio a la luz de mi pasado, mi presente y mis sueños futuros?"**.

#### 4. TÚ (You) — Reto Práctico de la Semana (5 min)
Ante la decisión que estás postergando esta semana, hazte la Pregunta de Integridad: *¿Cuál es la opción de la que estaré agradecido dentro de 5 años?*`,
    },
    guide: {
        title: "2. Guía de Discusión para Grupos Pequeños",
        badge: "Lista para enviar a líderes",
        preview: `### Guía de Grupo: Decisiones que Construyen Futuro

**1. Rompehielo (5 min):**
¿Cuál fue una compra impulsiva o moda del pasado de la que hoy te ríes al ver las fotos?

**2. Idea Central:**
La sabiduría no consiste solo en evitar lo malo, sino en elegir hoy lo que protege nuestro mañana.

**3. Preguntas Abiertas de Conversación (30 min):**
* Cuando estás cansado o bajo presión financiera/familiar, ¿qué área de tu vida tiende a sufrir primero?
* *Nota para el líder: Da espacio al silencio; comparte primero un ejemplo breve tuyo.*
* Leamos Efesios 5:15-16. ¿Por qué crees que nos cuesta tanto conectar nuestras decisiones de hoy con sus consecuencias a 5 años?
* Si pudieras darle un consejo a tu "yo" de hace 10 años sobre la familia o el dinero, ¿cuál sería?

**4. Paso Práctico de la Semana:**
Identifica un hábito de 15 minutos diarios que acerque tu hogar a la paz que deseas ver a fin de año.`,
    },
    kids: {
        title: "3. Lección de Niños y Familias",
        badge: "Primaria + Conexión con Padres",
        preview: `### Lección Infantil: Elegir con Sabiduría

**Verdad Básica:** Puedo confiar en Dios para tomar buenas decisiones.
**Frase Clave:** *"¡Pienso antes de actuar!"*

**Actividad de Apertura — El Puente de Vasos (10 min):**
En equipos, los niños construyen una torre con vasos plásticos. Luego retiran un vaso de la base para ver cómo una sola pieza afecta toda la torre. Así funcionan nuestras decisiones.

**Conexión para los Padres (WhatsApp del Domingo al Mediodía):**
*"¡Hola papás! Hoy en Niños aprendimos con Proverbios 27:12 que las personas sabias miran hacia adelante antes de decidir. Pregunta para el almuerzo de hoy: ¿Qué buena decisión tomaste esta semana de la que te sientes feliz?"*`,
    },
    runsheet: {
        title: "4. Orden del Servicio Dominical (Run Sheet 70m)",
        badge: "Formato Producción & Host",
        preview: `### Minuto a Minuto — Servicio Dominical (70 min)

| Minuto | Duración | Elemento | Responsable | Notas de Producción |
| :--- | :--- | :--- | :--- | :--- |
| -05:00 | 5m | Cuenta Regresiva | Media | Música ambiente cálida al 65%, luces de auditorio al 50% |
| 00:00 | 4m | Canción de Apertura | Banda | Energía alta, letras claras para invitados |
| 04:00 | 2m | Bienvenida del Host | Anfitrión | Luz puntual cálida, fondo de serie en pantalla |
| 06:00 | 12m | Bloque de Alabanza (2 canciones) | Banda | Transición fluida |
| 18:00 | 3m | Anuncio + Generosidad | Host | Video corto 60s + transición |
| 21:00 | 35m | Mensaje Dominical | Pastor | Reloj de escenario activo, grabación limpia |
| 56:00 | 5m | Canción de Respuesta y Cierre | Banda / Pastor | Invitación al Foyer para nuevos visitantes |

**Guion de Bienvenida del Host (Palabra por palabra):**
*"¡Muy buenos días! Qué alegría tenerlos hoy aquí. Especialmente si nos visitas por primera vez o hace años no pisabas una iglesia: queremos que sepas que diseñamos esta mañana pensando en ti..."*`,
    },
    social: {
        title: "5. Pack de Redes Sociales y Difusión de WhatsApp",
        badge: "Instagram + WhatsApp Viernes",
        preview: `### Mensaje de WhatsApp para toda la Iglesia (Viernes 6:00 PM)
*"¡Hola familia! 👋 ¿Alguna vez tomaste una decisión en caliente de la que luego te arrepentiste? Este domingo estrenamos un mensaje súper práctico: **'Cómo no ser tu peor enemigo'**. Es el domingo ideal para invitar a ese amigo o familiar que está por tomar una decisión importante. ¡Nos vemos a las 10:00 AM! Te guardamos lugar."*

### Guion de Reel / TikTok (30 seg)
* **Gancho (0-3s):** "La pregunta que más hogares ha destruido no es la que imaginas..."
* **Cuerpo (3-22s):** "Casi todos preguntamos: '¿Tiene algo de malo hacer esto?'. Pero nadie construye una gran familia o finanzas sanas viviendo al borde del precipicio. La pregunta correcta es: '¿Qué es lo más sabio para mi futuro?'."
* **Cierre (22-30s):** "Este domingo hablamos de cómo blindar tus decisiones. Te esperamos."`,
    },
};

export default function LandingPage() {
    const { token } = useAuthStore();
    const [activeSample, setActiveSample] = useState<keyof typeof SAMPLE_DELIVERABLES>("sermon");

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col">
            {/* Top Navigation */}
            <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur-md">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                        <div className="h-9 w-9 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-heading font-bold text-sm shadow-xs">
                            IA
                        </div>
                        <div>
                            <span className="font-heading font-bold text-base tracking-tight text-foreground block leading-none">
                                Irresistible Agent
                            </span>
                            <span className="text-[11px] text-muted-foreground font-medium">
                                Claridad, Recursos & Liderazgo
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {token ? (
                            <Link href="/dashboard">
                                <Button size="sm" className="font-semibold gap-1.5">
                                    Ir a mi Centro de Mando
                                    <ArrowRight className="h-4 w-4" />
                                </Button>
                            </Link>
                        ) : (
                            <>
                                <Link href="/login">
                                    <Button variant="ghost" size="sm" className="font-medium text-sm">
                                        Iniciar Sesión
                                    </Button>
                                </Link>
                                <Link href="/register">
                                    <Button size="sm" className="font-semibold gap-1.5">
                                        Probar 15 Días Gratis
                                        <ArrowRight className="h-3.5 w-3.5" />
                                    </Button>
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="py-14 md:py-20 px-4 sm:px-6 border-b border-border bg-gradient-to-b from-background via-background to-secondary/40">
                <div className="max-w-5xl mx-auto text-center space-y-6">
                    <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
                        <Sparkles className="h-3.5 w-3.5" />
                        Conectado a más de 1,800 recursos, series y manuales ministeriales
                    </div>

                    <h1 className="text-3xl sm:text-5xl md:text-6xl font-bold font-heading tracking-tight text-foreground leading-[1.12] max-w-4xl mx-auto">
                        Prepara todo el material de tu semana en{" "}
                        <span className="text-primary">3 minutos</span>, no en 15 horas.
                    </h1>

                    <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                        Diseñado para pastores, directores y <strong>líderes de cualquier área</strong> que buscan claridad y entrenamiento práctico. Produce todos los materiales de la semana en un clic, consulta a especialistas por área y entrena a tus equipos con <strong>Irresistible Agent</strong>.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                        <Link href={token ? "/studio" : "/register"}>
                            <Button size="lg" className="h-12 px-8 text-base font-semibold gap-2 shadow-sm">
                                <Sparkles className="h-4 w-4" />
                                Preparar mi Próxima Semana Gratis
                                <ArrowRight className="h-4 w-4" />
                            </Button>
                        </Link>
                        <Link href="/login">
                            <Button variant="outline" size="lg" className="h-12 px-6 text-base font-medium bg-card">
                                Ya tengo cuenta
                            </Button>
                        </Link>
                    </div>

                    <div className="pt-2 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
                        <span className="inline-flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                            15 días de prueba sin costo
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                            Exportación directa a Word (.docx) y PDF
                        </span>
                        <span className="inline-flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                            1,812 recursos de la Biblioteca incluidos
                        </span>
                    </div>
                </div>

                {/* Interactive Live Deliverable Showcase */}
                <div className="max-w-5xl mx-auto mt-12">
                    <Card className="border-border shadow-md bg-card overflow-hidden">
                        <div className="px-4 sm:px-6 py-3.5 bg-secondary/60 border-b border-border flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                                <span className="h-2.5 w-2.5 rounded-full bg-primary" />
                                <span className="text-xs font-bold uppercase tracking-wider text-foreground/80">
                                    Vista Previa Real — Lo que recibes en cada Pack Dominical:
                                </span>
                            </div>
                            <Badge variant="outline" className="text-[11px] bg-card">
                                Ejemplo: Serie &ldquo;Cómo no ser tu peor enemigo&rdquo;
                            </Badge>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-12">
                            {/* Left Tabs */}
                            <div className="md:col-span-4 border-b md:border-b-0 md:border-r border-border p-3 space-y-1.5 bg-secondary/20">
                                <button
                                    onClick={() => setActiveSample("sermon")}
                                    className={`w-full text-left px-3.5 py-3 rounded-lg text-xs font-semibold flex items-center gap-2.5 transition-all ${
                                        activeSample === "sermon"
                                            ? "bg-primary text-primary-foreground shadow-2xs"
                                            : "text-foreground/80 hover:bg-secondary"
                                    }`}
                                >
                                    <BookOpen className="h-4 w-4 shrink-0" />
                                    1. Bosquejo de Predicación
                                </button>
                                <button
                                    onClick={() => setActiveSample("guide")}
                                    className={`w-full text-left px-3.5 py-3 rounded-lg text-xs font-semibold flex items-center gap-2.5 transition-all ${
                                        activeSample === "guide"
                                            ? "bg-primary text-primary-foreground shadow-2xs"
                                            : "text-foreground/80 hover:bg-secondary"
                                    }`}
                                >
                                    <Users className="h-4 w-4 shrink-0" />
                                    2. Guía de Grupos Pequeños
                                </button>
                                <button
                                    onClick={() => setActiveSample("kids")}
                                    className={`w-full text-left px-3.5 py-3 rounded-lg text-xs font-semibold flex items-center gap-2.5 transition-all ${
                                        activeSample === "kids"
                                            ? "bg-primary text-primary-foreground shadow-2xs"
                                            : "text-foreground/80 hover:bg-secondary"
                                    }`}
                                >
                                    <Heart className="h-4 w-4 shrink-0" />
                                    3. Lección de Niños y Familia
                                </button>
                                <button
                                    onClick={() => setActiveSample("runsheet")}
                                    className={`w-full text-left px-3.5 py-3 rounded-lg text-xs font-semibold flex items-center gap-2.5 transition-all ${
                                        activeSample === "runsheet"
                                            ? "bg-primary text-primary-foreground shadow-2xs"
                                            : "text-foreground/80 hover:bg-secondary"
                                    }`}
                                >
                                    <Clock className="h-4 w-4 shrink-0" />
                                    4. Orden del Servicio (70m)
                                </button>
                                <button
                                    onClick={() => setActiveSample("social")}
                                    className={`w-full text-left px-3.5 py-3 rounded-lg text-xs font-semibold flex items-center gap-2.5 transition-all ${
                                        activeSample === "social"
                                            ? "bg-primary text-primary-foreground shadow-2xs"
                                            : "text-foreground/80 hover:bg-secondary"
                                    }`}
                                >
                                    <Share2 className="h-4 w-4 shrink-0" />
                                    5. Redes + WhatsApp Iglesia
                                </button>
                            </div>

                            {/* Right Document Preview */}
                            <div className="md:col-span-8 p-6 sm:p-8 bg-card space-y-4">
                                <div className="flex items-center justify-between border-b border-border pb-3">
                                    <h3 className="font-heading font-bold text-base text-foreground">
                                        {SAMPLE_DELIVERABLES[activeSample].title}
                                    </h3>
                                    <Badge variant="secondary" className="text-[11px]">
                                        {SAMPLE_DELIVERABLES[activeSample].badge}
                                    </Badge>
                                </div>
                                <div className="prose prose-sm max-w-none text-foreground/90 leading-relaxed font-sans prose-headings:font-heading prose-headings:text-foreground prose-strong:text-foreground">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {SAMPLE_DELIVERABLES[activeSample].preview}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </section>

            {/* 3 Core Pillars */}
            <section className="py-16 px-4 sm:px-6 max-w-6xl mx-auto space-y-10">
                <div className="text-center max-w-2xl mx-auto space-y-2">
                    <h2 className="text-2xl sm:text-3xl font-bold font-heading">
                        Claridad, Recursos y Entrenamiento para Todo tu Equipo
                    </h2>
                    <p className="text-sm text-muted-foreground">
                        Desde el pastor principal hasta cada líder de grupo pequeño, maestro de niños, anfitrión de bienvenida y voluntario de producción.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="border-border bg-card shadow-2xs">
                        <CardHeader>
                            <div className="h-11 w-11 rounded-xl bg-primary/12 text-primary flex items-center justify-center mb-2">
                                <Library className="h-5 w-5" />
                            </div>
                            <CardTitle className="text-lg font-heading">
                                Biblioteca de 1,812 Recursos
                            </CardTitle>
                            <CardDescription className="text-xs leading-relaxed">
                                Acceso directo al catálogo completo de series, currículos, manuales de voluntarios y guías prácticas, listos para traducir y adaptar a tu contexto hispano.
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-border bg-card shadow-2xs">
                        <CardHeader>
                            <div className="h-11 w-11 rounded-xl bg-primary/12 text-primary flex items-center justify-center mb-2">
                                <Users className="h-5 w-5" />
                            </div>
                            <CardTitle className="text-lg font-heading">
                                Consulta con los Especialistas
                            </CardTitle>
                            <CardDescription className="text-xs leading-relaxed">
                                Consulta individualmente o reúne en Consejo Directivo a expertos en Predicación, Niños y Familia, Jóvenes, Grupos Pequeños, Servicios a Invitados, Producción y Generosidad.
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-border bg-card shadow-2xs">
                        <CardHeader>
                            <div className="h-11 w-11 rounded-xl bg-primary/12 text-primary flex items-center justify-center mb-2">
                                <Swords className="h-5 w-5" />
                            </div>
                            <CardTitle className="text-lg font-heading">
                                Entrenamiento de Líderes
                            </CardTitle>
                            <CardDescription className="text-xs leading-relaxed">
                                Entrena a tus líderes y voluntarios practicando conversaciones reales difíciles (padres en el área infantil, voluntarios agotados, visitas nuevas) con evaluación pastoral inmediata.
                            </CardDescription>
                        </CardHeader>
                    </Card>
                </div>
            </section>

            {/* Pricing & ROI Section */}
            <section className="py-16 px-4 sm:px-6 bg-secondary/40 border-t border-border">
                <div className="max-w-4xl mx-auto">
                    <Card className="border-primary/30 bg-card shadow-md overflow-hidden">
                        <div className="grid grid-cols-1 md:grid-cols-12 items-center">
                            <div className="md:col-span-7 p-6 sm:p-8 space-y-4">
                                <Badge className="bg-primary/15 text-primary hover:bg-primary/20 border-0">
                                    Membresía Todo Incluido para tu Equipo
                                </Badge>
                                <h3 className="text-2xl font-bold font-heading">
                                    Ahorra más de 12 horas cada semana en preparación ministerial
                                </h3>
                                <ul className="space-y-2.5 text-xs sm:text-sm text-foreground/90">
                                    <li className="flex items-center gap-2.5">
                                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                                        Generador ilimitado en Prepara tu Semana (5 documentos listos)
                                    </li>
                                    <li className="flex items-center gap-2.5">
                                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                                        Buscador y adaptador de las 1,812 series y guías de la Biblioteca Irresistible Agent
                                    </li>
                                    <li className="flex items-center gap-2.5">
                                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                                        Acceso ilimitado a los 11 Especialistas, Análisis de Documentos y Modo Consejo
                                    </li>
                                    <li className="flex items-center gap-2.5">
                                        <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
                                        Centro de Entrenamiento para capacitar a líderes de cualquier área
                                    </li>
                                </ul>
                            </div>

                            <div className="md:col-span-5 p-6 sm:p-8 bg-secondary/50 border-t md:border-t-0 md:border-l border-border text-center space-y-4">
                                <div>
                                    <span className="text-xs uppercase font-bold tracking-wider text-muted-foreground">
                                        Suscripción Mensual
                                    </span>
                                    <div className="text-4xl font-bold font-heading text-foreground mt-1">
                                        $9.99 <span className="text-sm font-normal text-muted-foreground">USD / mes</span>
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Incluye 15 días de prueba gratuita. Cancela cuando quieras.
                                    </p>
                                </div>

                                <Link href="/register" className="block">
                                    <Button size="lg" className="w-full font-semibold gap-2">
                                        Comenzar Prueba de 15 Días
                                        <ArrowRight className="h-4 w-4" />
                                    </Button>
                                </Link>

                                <div className="flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground">
                                    <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                                    Garantía de satisfacción para tu iglesia
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 px-4 border-t border-border text-center text-xs text-muted-foreground">
                <p>© {new Date().getFullYear()} Irresistible Agent — Claridad, Recursos y Liderazgo Ministerial.</p>
            </footer>
        </div>
    );
}
