import datetime
from random import randint  # Random number generation for economy

# Peacock economy module - names
upgrade_name_dict = {
    "cookie_jar_storage_level": "Банк",
    "upgrade1": "Друг павлиновод",
    "upgrade2": "Просторный загон",
    "upgrade3": "Белый павлин",
    "upgrade4": "Конголезский павлин",
    "upgrade5": "Зелёный павлин",
    "upgrade6": "Чернокрылый павлин",
    "upgrade7": "Ферма павлинов",
}

# Peacock shop - Roles
archive_role = 665992090601127973
sin_writer_role = 685185862417514597
# Elite roles
pride_role = 912325373151305740
dutch_role = 799550562189180929
prussian_role = 984803794611232858
dzen_role = 796400397694140456
ottoman_role = 833636935876345906

# Peacock shop - role/price dictionary
shop_role_pricelist = {
    archive_role: 10000,
    sin_writer_role: 50000,
    pride_role: 10000,
    dutch_role: 10000,
    prussian_role: 10000,
    dzen_role: 10000,
    ottoman_role: 10000,
}

# Peacock economy - cooldowns
peacock_gain_per_message_cooldown = 10
daily_bonus_cooldown = 24 * 3600
weekly_bonus_cooldown = 7 * 24 * 3600
monthly_bonus_cooldown = 30 * 24 * 3600
work_bonus_cooldown = 2 * 3600
theft_cooldown = 10 * 60

# Peacock economy - peacock gain
gain_from_upgrade_dict = {
    "upgrade1": 5,
    "upgrade2": 15,
    "upgrade3": 35,
    "upgrade4": 75,
    "upgrade5": 170,
    "upgrade6": 370,
    "upgrade7": 495,
}

daily_bonus_ = 400
weekly_bonus_ = 750
monthly_bonus_ = 1500
bank_capacity_per_lvl_default = 400

# Peacock economy - item shop
item_dict = {
    "lockpicks": 5000,
}
item_name_dict = {
    "lockpicks": "Отмычка",
}

# Ascescion requirements
ascend_legal_path_min_lvls = 5


# Peacock economy - formulas
def price_bank_formula(level: int) -> int: return round(200 * 1.75 ** level)
def price_upgrade1_formula(level: int) -> int: return 200 + level * 30
def price_upgrade2_formula(level: int) -> int: return 400 + level * 60
def price_upgrade3_formula(level: int) -> int: return 800 + level * 90
def price_upgrade4_formula(level: int) -> int: return 1600 + level * 120
def price_upgrade5_formula(level: int) -> int: return 3200 + level * 150
def price_upgrade6_formula(level: int) -> int: return 6400 + level * 180
def price_upgrade7_formula(level: int) -> int: return 12800 + level * 210


upgrade_prices_functions_dict = {
    "cookie_jar_storage_level": price_bank_formula,
    "upgrade1": price_upgrade1_formula,
    "upgrade2": price_upgrade2_formula,
    "upgrade3": price_upgrade3_formula,
    "upgrade4": price_upgrade4_formula,
    "upgrade5": price_upgrade5_formula,
    "upgrade6": price_upgrade6_formula,
    "upgrade7": price_upgrade7_formula,
}


def peacocks_gained_per_message() -> int:
    return randint(0, 12)


def steal_cookies(cookies_: int) -> int:
    return int(randint(5, 65) / 100 * cookies_)


def steal_cookies_failure(cookies_: int) -> int:
    return int(randint(5, 15) / 100 * cookies_)


# Timezone
def moscow_timezone() -> datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=3)
