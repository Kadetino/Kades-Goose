import sqlite3 as sl  # SQLite database
import cog_settings.peacock_economy_settings as loc
import discord


def add_new_user_to_economy_db(sql_connection: sl.Connection, guild_id: int, user_id: int) -> None:
    """Database: adding entries"""
    sql_connection.execute(
        "INSERT OR IGNORE INTO ECONOMY (guild_id, user_id, cookie_counter, cookie_jar_storage, cookie_jar_storage_level, upgrade1, upgrade2, upgrade3, upgrade4, upgrade5, upgrade6, upgrade7, last_access, daily_bonus, weekly_bonus, monthly_bonus, message_cooldown, last_theft_attempt, infamy_lvl, fame_lvl, last_robbed, lockpicks) VALUES (?,?,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
        (guild_id, user_id))


def get_user_column_info(sql_connection: sl.Connection, guild_id: int, user_id: int, upgrade: str) -> int:
    """Database: retrieve information from column"""
    return sql_connection.execute(
        f"SELECT {upgrade} FROM ECONOMY WHERE guild_id = {guild_id} AND user_id = {user_id}").fetchone()[0]


def deposit_peacocks_in_bank(sql_connection: sl.Connection, guild_id: int, user_id: int, amount: int) -> None:
    """Database: bank deposits and withdrawals"""
    sql_connection.execute(
        f"UPDATE ECONOMY SET cookie_counter = cookie_counter - {amount} WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id))
    sql_connection.execute(
        f"UPDATE ECONOMY SET cookie_jar_storage = cookie_jar_storage + {amount} WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id))
    sql_connection.commit()


def claim_peacock_bonus(sql_connection: sl.Connection, guild_id: int, user_id: int, upgrade: str, amount: int, epoch_right_now: int) -> None:
    """Database: claiming bonuses and setting new cooldown"""
    sql_connection.execute(
        f"UPDATE ECONOMY SET {upgrade} = {epoch_right_now} WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id))
    sql_connection.execute(
        f"UPDATE ECONOMY SET cookie_counter = cookie_counter + {amount} WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id))
    sql_connection.commit()


def bank_capacity_per_lvl(ctx: discord.Interaction) -> int:
    # Database connection
    sql_connection = sl.connect('Peacock.db')

    # Info retrieval
    infamy_lvl = get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "infamy_lvl")
    fame_lvl = get_user_column_info(sql_connection, ctx.guild.id, ctx.user.id, "fame_lvl")

    # Close
    sql_connection.close()

    return round(loc.bank_capacity_per_lvl_default * (1 + 0.05*fame_lvl + 0.15*infamy_lvl))
