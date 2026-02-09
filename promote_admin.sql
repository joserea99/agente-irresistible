-- Busca tu usuario en Authentication y crea/actualiza su perfil
INSERT INTO public.profiles (id, username, full_name, role, subscription_status)
SELECT id, email, raw_user_meta_data->>'full_name', 'admin', 'active'
FROM auth.users
WHERE email = 'jose.rea@lbne.org' -- TU CORREO AQUÍ
ON CONFLICT (id) DO UPDATE
SET role = 'admin', subscription_status = 'active';
