import datetime

# Peacock economy module - names
upg1 = "Друг павлиновод"
upg2 = "Просторный загон"
upg3 = "Белый павлин"
upg4 = "Конголезский павлин"
upg5 = "Зелёный павлин"
upg6 = "Чернокрылый павлин"
upg7 = "Ферма павлинов"

# Peacock shop - Roles
archive_role = 665992090601127973
sin_writer_role = 685185862417514597
# Elite roles
pride_role = 912325373151305740
dutch_role = 799550562189180929
prussian_role = 984803794611232858
dzen_role = 796400397694140456
ottoman_role = 833636935876345906

# # testing - goose refuge
# # Peacock shop - Roles
# archive_role = 966010231270281246
# sin_writer_role = 966010406487339098
# # Elite roles
# pride_role = 966010793260904489
# dutch_role = 966010231270281246
# prussian_role = 966010406487339098
# dzen_role = 966010793260904489
# ottoman_role = 966010231270281246

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


# Timezone
def moscow_timezone() -> datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=3)
