-- Роли и профиль пользователя
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'kot';
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(200);
CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);

-- Пример назначения ролей (замените username на свои):
-- UPDATE users SET role = 'admin' WHERE username = 'admin';
-- UPDATE users SET role = 'ezh' WHERE username = 'ezh';
