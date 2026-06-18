-- ============================================================
-- MIGRACIÓN 002: Row-Level Security (RLS) en todas las tablas
-- Ejecutar en: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- ============================================================
-- 1. TABLA: profiles
-- ============================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Los usuarios sólo ven y editan su propio perfil
CREATE POLICY "profiles: usuario ve su propio perfil"
  ON public.profiles FOR SELECT
  USING (id = auth.uid());

CREATE POLICY "profiles: usuario edita su propio perfil"
  ON public.profiles FOR UPDATE
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

-- El backend (service_role) tiene acceso total
CREATE POLICY "profiles: service_role acceso total"
  ON public.profiles FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- 2. TABLA: chat_sessions
-- ============================================================
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

-- Los usuarios sólo ven sus propias sesiones de chat
CREATE POLICY "chat_sessions: usuario ve sus sesiones"
  ON public.chat_sessions FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "chat_sessions: usuario crea sus sesiones"
  ON public.chat_sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "chat_sessions: usuario elimina sus sesiones"
  ON public.chat_sessions FOR DELETE
  USING (user_id = auth.uid());

CREATE POLICY "chat_sessions: service_role acceso total"
  ON public.chat_sessions FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- 3. TABLA: chat_messages
-- ============================================================
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Los usuarios sólo ven los mensajes de sus propias sesiones
CREATE POLICY "chat_messages: usuario ve sus mensajes"
  ON public.chat_messages FOR SELECT
  USING (
    session_id IN (
      SELECT id FROM public.chat_sessions WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "chat_messages: usuario crea mensajes en sus sesiones"
  ON public.chat_messages FOR INSERT
  WITH CHECK (
    session_id IN (
      SELECT id FROM public.chat_sessions WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "chat_messages: service_role acceso total"
  ON public.chat_messages FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- 4. TABLA: documents
-- ============================================================
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Los documentos de knowledge base son visibles para usuarios autenticados
-- (son recursos compartidos de la iglesia, no privados por usuario)
CREATE POLICY "documents: usuarios autenticados pueden leer"
  ON public.documents FOR SELECT
  USING (auth.role() = 'authenticated');

-- Solo el service_role puede insertar/actualizar/eliminar documentos
CREATE POLICY "documents: service_role gestiona documentos"
  ON public.documents FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- 5. TABLA: document_chunks
-- ============================================================
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

-- Los chunks son visibles para usuarios autenticados (igual que documentos)
CREATE POLICY "document_chunks: usuarios autenticados pueden leer"
  ON public.document_chunks FOR SELECT
  USING (auth.role() = 'authenticated');

-- Solo el service_role puede insertar/actualizar/eliminar chunks
CREATE POLICY "document_chunks: service_role gestiona chunks"
  ON public.document_chunks FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- 6. TABLA: dojo_completions
-- ============================================================
ALTER TABLE public.dojo_completions ENABLE ROW LEVEL SECURITY;

-- Los usuarios sólo ven sus propios completions del dojo
CREATE POLICY "dojo_completions: usuario ve sus completions"
  ON public.dojo_completions FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "dojo_completions: usuario crea sus completions"
  ON public.dojo_completions FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "dojo_completions: service_role acceso total"
  ON public.dojo_completions FOR ALL
  USING (auth.role() = 'service_role');

-- ============================================================
-- VERIFICACIÓN: Ver estado RLS de todas las tablas
-- (Puedes ejecutar esto después para confirmar)
-- ============================================================
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY tablename;
