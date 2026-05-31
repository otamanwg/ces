-- Базова схема бази даних для MVP Економічного Онлайн-Симулятора "Місто"
-- СУБД: PostgreSQL

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. ТАБЛИЦЯ МІСТА (СЕРВЕРИ)
CREATE TABLE cities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    treasury_balance DECIMAL(15, 2) NOT NULL DEFAULT 50000.00, -- Скарбниця міста
    tax_rate_income DECIMAL(5, 2) NOT NULL DEFAULT 10.00,       -- Прибутковий податок (у %)
    tax_rate_property DECIMAL(5, 2) NOT NULL DEFAULT 2.00,     -- Податок на майно/бізнес (у %)
    inflation_rate DECIMAL(5, 2) NOT NULL DEFAULT 0.00,        -- Поточна інфляція на сервері (у %)
    mayor_player_id UUID,                                       -- ID чинного Мера
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. ТАБЛИЦЯ ГРАВЦІВ
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE RESTRICT,
    username VARCHAR(50) NOT NULL UNIQUE,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 500.00,            -- Стартовий капітал
    energy INT NOT NULL DEFAULT 100 CHECK (energy >= 0 AND energy <= 100),
    mood INT NOT NULL DEFAULT 100 CHECK (mood >= 0 AND mood <= 100),
    education_level VARCHAR(50) NOT NULL DEFAULT 'High School', -- 'High School', 'College', 'University'
    diploma_verified BOOLEAN NOT NULL DEFAULT TRUE,            -- FALSE, якщо диплом підроблений
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Додаємо зовнішній ключ для Мера в таблицю міст після створення таблиці гравців
ALTER TABLE cities ADD CONSTRAINT fk_mayor FOREIGN KEY (mayor_player_id) REFERENCES players(id) ON DELETE SET NULL;

-- 3. ТАБЛИЦЯ ПІДПРИЄМСТВ (БІЗНЕСІВ)
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,                                  -- 'utility_water', 'utility_housing', 'shop', 'factory', 'private_hostel'
    owner_player_id UUID REFERENCES players(id) ON DELETE SET NULL, -- NULL для державних/ботівських
    owner_share_pct DECIMAL(5, 2) NOT NULL DEFAULT 100.00,      -- Частка власності (для держ. підприємств макс. 49%)
    cash_balance DECIMAL(15, 2) NOT NULL DEFAULT 10000.00,      -- Бюджет компанії
    status VARCHAR(20) NOT NULL DEFAULT 'active',               -- 'active', 'bankrupt', 'damaged' (після стихійного лиха)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. ТАБЛИЦЯ ВАКАНСІЙ ТА РОБОТИ
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,                                -- Назва посади (напр., 'Сантехнік Водоканалу')
    salary_per_hour DECIMAL(10, 2) NOT NULL,                    -- Погодинна оплата (брутто)
    min_education VARCHAR(50) NOT NULL DEFAULT 'High School',   -- Вимоги до освіти
    energy_cost_per_shift INT NOT NULL DEFAULT 30,              -- Скільки енергії забирає зміна
    filled_by_player_id UUID UNIQUE REFERENCES players(id) ON DELETE SET NULL, -- NULL, якщо вакансія вільна
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. ТАБЛИЦЯ ХОСТЕЛІВ ТА ОРЕНДИ
CREATE TABLE hostels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, -- Фірма-власник хостелу
    room_number INT NOT NULL,
    rent_price_per_day DECIMAL(10, 2) NOT NULL DEFAULT 15.00,   -- Ціна за 1 ігровий день
    energy_regen_per_hour INT NOT NULL DEFAULT 10,              -- Відновлення енергії за годину сну
    tenant_player_id UUID UNIQUE REFERENCES players(id) ON DELETE SET NULL, -- NULL, якщо кімната вільна
    UNIQUE(business_id, room_number)
);

-- 6. ЛОГУВАННЯ ТРАНЗАКЦІЙ (Для аналітики та контролю інфляції)
CREATE TABLE transactions_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,                                    -- Може бути ID гравця, фірми або скарбниці
    sender_type VARCHAR(20) NOT NULL,                           -- 'player', 'business', 'treasury', 'system'
    receiver_id UUID NOT NULL,
    receiver_type VARCHAR(20) NOT NULL,                         -- 'player', 'business', 'treasury', 'system'
    amount DECIMAL(15, 2) NOT NULL,
    tax_deducted DECIMAL(15, 2) NOT NULL DEFAULT 0.00,          -- Податок, стягнутий у Скарбницю
    purpose VARCHAR(100) NOT NULL,                              -- 'salary', 'rent', 'tax_payment', 'license_purchase', 'trade_goods'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. ТАБЛИЦЯ ДЛЯ ТІНЬОВИХ ПРАВОПОРУШЕНЬ (ДЛЯ ПОЛІЦІЇ)
CREATE TABLE police_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    offense_type VARCHAR(100) NOT NULL,                         -- 'fake_diploma', 'unlicensed_business', 'tax_evasion'
    fine_amount DECIMAL(10, 2),                                 -- Накладений штраф
    status VARCHAR(20) NOT NULL DEFAULT 'under_investigation',  -- 'under_investigation', 'fined', 'imprisoned', 'case_closed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. ТАБЛИЦЯ ДОМАШНІХ УЛУБЛЕНЦІВ (PETS)
CREATE TABLE pets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(30) NOT NULL,                                  -- 'dog', 'cat', 'raccoon', 'robotic'
    breed VARCHAR(50) NOT NULL,                                 -- Порода (напр., 'Shepherd', 'Siamese')
    hunger INT NOT NULL DEFAULT 0 CHECK (hunger >= 0 AND hunger <= 100),   -- Ситість (0 - ситий, 100 - голодний)
    health INT NOT NULL DEFAULT 100 CHECK (health >= 0 AND health <= 100),
    loyalty INT NOT NULL DEFAULT 50 CHECK (loyalty >= 0 AND loyalty <= 100),
    status VARCHAR(20) NOT NULL DEFAULT 'active',               -- 'active', 'sick', 'shelter_lost' (втік у притулок)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. ТАБЛИЦЯ СПОРТИВНИХ КЛУБІВ (SPORTS CLUBS)
CREATE TABLE sports_clubs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL UNIQUE,
    sport_type VARCHAR(30) NOT NULL,                            -- 'football', 'baseball', 'basketball', 'cybersport'
    owner_player_id UUID REFERENCES players(id) ON DELETE SET NULL, -- NULL, якщо клуб під управлінням ШІ
    cash_balance DECIMAL(15, 2) NOT NULL DEFAULT 50000.00,      -- Бюджет клубу
    stadium_capacity INT NOT NULL DEFAULT 5000,                 -- Місткість стадіону
    ticket_price DECIMAL(10, 2) NOT NULL DEFAULT 10.00,         -- Ціна квитка на матч
    training_efficiency DECIMAL(5, 2) NOT NULL DEFAULT 1.00,    -- Якість тренувань (множник)
    league_points INT NOT NULL DEFAULT 0,                       -- Поточні очки в сезоні
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. ТАБЛИЦЯ СПОРТИВНИХ КОНТРАКТІВ ГРАВЦІВ
CREATE TABLE player_athlete_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL UNIQUE REFERENCES players(id) ON DELETE CASCADE,
    club_id UUID NOT NULL REFERENCES sports_clubs(id) ON DELETE CASCADE,
    salary_per_match DECIMAL(10, 2) NOT NULL DEFAULT 200.00,    -- Оплата за зіграний матч
    role VARCHAR(30) NOT NULL DEFAULT 'player',                 -- 'player', 'star_player', 'coach'
    contract_status VARCHAR(20) NOT NULL DEFAULT 'active',      -- 'active', 'bench', 'expired'
    strength_stat INT NOT NULL DEFAULT 10 CHECK (strength_stat >= 0),
    stamina_stat INT NOT NULL DEFAULT 10 CHECK (stamina_stat >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. ТАБЛИЦЯ КРЕДИТІВ ТА ЗАСТАВ (BANK LOANS)
CREATE TABLE bank_loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    principal_amount DECIMAL(15, 2) NOT NULL,                   -- Тіло кредиту
    remaining_debt DECIMAL(15, 2) NOT NULL,                     -- Залишок боргу
    daily_payment DECIMAL(10, 2) NOT NULL,                      -- Щоденний обов'язковий платіж
    status VARCHAR(20) NOT NULL DEFAULT 'active',               -- 'active', 'delinquent' (прострочений), 'defaulted' (дефолт)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. ТАБЛИЦЯ СТРАХОВИХ ПОЛІСІВ (INSURANCE POLICIES)
CREATE TABLE insurance_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE, -- Застрахована фірма (опціонально)
    provider_business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE RESTRICT, -- Страхова фірма гравця
    coverage_amount DECIMAL(15, 2) NOT NULL,                    -- Сума покриття
    daily_premium DECIMAL(10, 2) NOT NULL,                      -- Щоденний страховий внесок
    status VARCHAR(20) NOT NULL DEFAULT 'active',               -- 'active', 'claimed', 'expired'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. ТАБЛИЦЯ ПРОФСПІЛОК (LABOR UNIONS)
CREATE TABLE labor_unions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL UNIQUE REFERENCES businesses(id) ON DELETE CASCADE, -- Де діє профспілка
    name VARCHAR(100) NOT NULL,
    strike_active BOOLEAN NOT NULL DEFAULT FALSE,               -- Чи триває страйк зараз
    strike_ends_at TIMESTAMP WITH TIME ZONE,                    -- Коли закінчується страйк
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. ТАБЛИЦЯ КАРТЕЛІВ (LOBBYING CARTELS)
CREATE TABLE cartels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    industry_type VARCHAR(50) NOT NULL,                         -- 'transport', 'factory', 'retail'
    lobby_fund DECIMAL(15, 2) NOT NULL DEFAULT 0.00,             -- Фонд лобіювання
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. ТАБЛИЦЯ МІСЬКОГО ТРАНСПОРТУ (CITY TRANSPORTS)
CREATE TABLE transports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    city_id UUID NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL,                                  -- 'bus', 'tram', 'subway', 'taxi_fleet'
    name VARCHAR(100) NOT NULL,
    owner_player_id UUID REFERENCES players(id) ON DELETE SET NULL, -- NULL для державного транспорту
    ticket_price DECIMAL(10, 2) NOT NULL DEFAULT 2.00,          -- Вартість проїзду
    passenger_capacity INT NOT NULL DEFAULT 100,                -- Пропускна здатність за зміну
    maintenance_cost DECIMAL(10, 2) NOT NULL DEFAULT 50.00,     -- Щоденні витрати на обслуговування
    operational_status VARCHAR(20) NOT NULL DEFAULT 'active',   -- 'active', 'inactive', 'overloaded'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
