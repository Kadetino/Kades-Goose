import datetime

# Peacock economy module
upg1 = "Друг павлиновод"
upg2 = "Просторный загон"
upg3 = "Белый павлин"
upg4 = "Конголезский павлин"
upg5 = "Зелёный павлин"
upg6 = "Чернокрылый павлин"
upg7 = "Ферма павлинов"


# Timezone
def moscow_timezone() -> datetime:
    return datetime.datetime.utcnow() + datetime.timedelta(hours=3)
