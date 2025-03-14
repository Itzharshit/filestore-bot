import os
import time
import math
import json
import string
import random
import traceback
import asyncio
import datetime
import aiofiles
from random import choice
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, \
    PeerIdInvalid
from configs import Config
from database import Database

BOT_USERNAME = Config.BOT_USERNAME
BOT_TOKEN = Config.BOT_TOKEN
API_ID = Config.API_ID
API_HASH = Config.API_HASH
DB_CHANNEL = Config.DB_CHANNEL
HOME_TEXT = Config.HOME_TEXT
UR_CHANNEL = Config.UR_CHANNEL
UR_GROUP = Config.UR_GROUP
BOT_OWNER = Config.BOT_OWNER
FORWARD_AS_COPY = Config.FORWARD_AS_COPY
db = Database(Config.DATABASE_URL, BOT_USERNAME)
broadcast_ids = {}
Bot = Client(BOT_USERNAME, bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)


async def send_msg(user_id, message):
    try:
        await message.forward(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception as e:
        return 500, f"{user_id} : {traceback.format_exc()}\n"


async def foo(bot, cmd):
    chat_id = cmd.from_user.id
    if not await db.is_user_exist(chat_id):
        await db.add_user(chat_id)
        await bot.send_message(
            Config.LOG_CHANNEL,
            f"#NEW_USER: \n\nNew User [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id}) started @{BOT_USERNAME} !!"
        )

    ban_status = await db.get_ban_status(chat_id)
    if ban_status["is_banned"]:
        if (
                datetime.date.today() - datetime.date.fromisoformat(ban_status["banned_on"])
        ).days > ban_status["ban_duration"]:
            await db.remove_ban(chat_id)
        else:
            await cmd.reply_text("You are Banned.", quote=True)
            return
    await cmd.continue_propagation()


@Bot.on_message(filters.private)
async def _(bot, cmd):
    await foo(bot, cmd)


@Bot.on_message(filters.command("start") & filters.private)
async def start(bot, cmd):
    if cmd.from_user.id in Config.BANNED_USERS:
        await cmd.reply_text("Sorry, You are banned.")
        return
    usr_cmd = cmd.text.split("_")[-1]
    if usr_cmd == "/start":
        if not Config.UPDATES_CHANNEL is None:
            invite_link = await bot.create_chat_invite_link(int(Config.UPDATES_CHANNEL))
            try:
                user = await bot.get_chat_member(int(Config.UPDATES_CHANNEL), cmd.from_user.id)
                if user.status == "kicked":
                    await bot.send_message(
                        chat_id=cmd.from_user.id,
                        text="Sorry, You are Banned.",
                        parse_mode="markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="PLEASE JOIN MY UPDATES CHANNEL IN ORDER TO USE ME!",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Join Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("Refresh", callback_data="refreshmeh")
                            ]
                        ]
                    ),
                    parse_mode="markdown"
                )
                return
            except Exception:
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="Something went Wrong.",
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return
        await cmd.reply_text(
            HOME_TEXT.format(cmd.from_user.first_name, cmd.from_user.id),
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Support Group", url=f"https://telegram.me/{UR_GROUP}"),
                        InlineKeyboardButton("Bots Channel", url=f"https://telegram.me/{UR_CHANNEL}")
                    ],
                  
                ]
            )
        )
    else:
        if not Config.UPDATES_CHANNEL is None:
            invite_link = await bot.create_chat_invite_link(int(Config.UPDATES_CHANNEL))
            try:
                user = await bot.get_chat_member(int(Config.UPDATES_CHANNEL), cmd.from_user.id)
                if user.status == "kicked":
                    await bot.send_message(
                        chat_id=cmd.from_user.id,
                        text="Sorry, You are Banned.",
                        parse_mode="markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                file_id = int(usr_cmd)
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="PLEASE JOIN MY UPDATES CHANNEL IN ORDER TO USE ME!",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Join Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("Refresh",
                                                     url=f"https://telegram.me/{BOT_USERNAME}?start={UR_CHANNEL}_{file_id}")
                            ]
                        ]
                    ),
                    parse_mode="markdown"
                )
                return
            except Exception:
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="Something went Wrong.",
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return
        try:
            file_id = int(usr_cmd)
            send_stored_file = None
            if FORWARD_AS_COPY is True:
                send_stored_file = await bot.copy_message(chat_id=cmd.from_user.id, protect_content=True, from_chat_id=DB_CHANNEL,
                                                          message_id=file_id)
            elif FORWARD_AS_COPY is False:
                send_stored_file = await bot.forward_messages(chat_id=cmd.from_user.id, protect_content=True, from_chat_id=DB_CHANNEL,
                                                              message_ids=file_id)
            await send_stored_file.reply_text(
                f"**Here is Sharable Link of this file:** https://telegram.me/{BOT_USERNAME}?start={UR_CHANNEL}_{file_id}\n\n__To Retrive the Stored File, just open the link!__",
                disable_web_page_preview=True, quote=True)
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")



@Bot.on_message(filters.document | filters.video | filters.audio & ~filters.edited)
async def main(bot, message):
    if message.chat.type == "private":
        if not Config.UPDATES_CHANNEL is None:
            invite_link = await bot.create_chat_invite_link(int(Config.UPDATES_CHANNEL))
            try:
                user = await bot.get_chat_member(int(Config.UPDATES_CHANNEL), message.from_user.id)
                if user.status == "kicked":
                    await bot.send_message(
                        chat_id=message.from_user.id,
                        text="Sorry Sir, You are Banned.",
                        parse_mode="markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text="**PLEASE JOIN MY UPDATES CHANNEL IN ORDER TO USE ME!",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Join Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("Refresh", callback_data="refreshmeh")
                            ]
                        ]
                    ),
                    parse_mode="markdown"
                )
                return
            except Exception:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text="Something went Wrong.",
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return

        if message.from_user.id in Config.BANNED_USERS:
            await message.reply_text("Sorry, You are banned!",
                                     disable_web_page_preview=True)
            return
        if Config.OTHER_USERS_CAN_SAVE_FILE is False:
            return
        editable = await message.reply_text("Please wait ...")
        try:
            forwarded_msg = await message.forward(DB_CHANNEL)
            file_er_id = forwarded_msg.message_id
            await forwarded_msg.reply_text(
                f"#PRIVATE_FILE:\n\n[{message.from_user.first_name}](tg://user?id={message.from_user.id}) Got File Link!",
                parse_mode="Markdown", disable_web_page_preview=True)
            share_link = f"https://telegram.me/{BOT_USERNAME}?start={UR_CHANNEL}_{file_er_id}"
            await editable.edit(
                f"**Your file is successfully stored!**\n\nHere is the Permanent Link of your file: {share_link}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Open Link", url=share_link)],
                     [InlineKeyboardButton("Bots Channel", url=f"https://telegram.me/{UR_CHANNEL}"),
                      InlineKeyboardButton("Support Group", url=f"https://telegram.me/{UR_GROUP}")]]
                ),
                disable_web_page_preview=True
            )
        except Exception as err:
            await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
    elif message.chat.type == "channel":
        if message.chat.id == Config.LOG_CHANNEL:
            return
        elif message.chat.id == int(Config.UPDATES_CHANNEL):
            return
        elif int(message.chat.id) in Config.BANNED_CHAT_IDS:
            await bot.leave_chat(message.chat.id)
            return
        else:
            pass
        forwarded_msg = None
        file_er_id = None
        if message.forward_from_chat:
            return
        elif message.forward_from:
            return
        else:
            pass
        if message.photo:
            return
        try:
            forwarded_msg = await message.forward(DB_CHANNEL)
            file_er_id = forwarded_msg.message_id
            share_link = f"https://telegram.me/{BOT_USERNAME}?start={UR_CHANNEL}_{file_er_id}"
            CH_edit = await bot.edit_message_reply_markup(message.chat.id, message.message_id,
                                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                                                              "Get Sharable Stored Link", url=share_link)]]))
            if message.chat.username:
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/{message.chat.username}/{CH_edit.message_id}) Channel's Broadcasted File's Button Added!")
            else:
                private_ch = str(message.chat.id)[4:]
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/c/{private_ch}/{CH_edit.message_id}) Channel's Broadcasted File's Button Added!")
        except Exception as err:
            print(f"Error: {err}")

@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(BOT_OWNER) & filters.reply)
async def broadcast_(c, m):
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    while True:
        broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break
    out = await m.reply_text(
        text=f"Broadcast Started! You will be notified with log file when all the users are notified."
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )
    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        async for user in all_users:
            sts, msg = await send_msg(
                user_id=int(user['id']),
                message=broadcast_msg
            )
            if msg is not None:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            if sts == 400:
                await db.delete_user(user['id'])
            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(
                        current=done,
                        failed=failed,
                        success=success
                    )
                )
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    else:
        await m.reply_document(
            document='broadcast.txt',
            caption=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    os.remove('broadcast.txt')


@Bot.on_message(filters.private & filters.command("status") & filters.user(BOT_OWNER))
async def sts(c, m):
    total_users = await db.total_users_count()
    await m.reply_text(text=f"**Total Users in DB:** `{total_users}`", parse_mode="Markdown", quote=True)


@Bot.on_message(filters.private & filters.command("ban") & filters.user(BOT_OWNER))
async def ban(c, m):
    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to ban any user from the bot.\n\nUsage:\n\n`/ban user_id ban_duration ban_reason`\n\nEg: `/ban 1234567 28 You misused me.`\n This will ban user with id `1234567` for `28` days for the reason `You misused me`.",
            quote=True
        )
        return
    try:
        user_id = int(m.command[1])
        ban_duration = int(m.command[2])
        ban_reason = ' '.join(m.command[3:])
        ban_log_text = f"Banning user {user_id} for {ban_duration} days for the reason {ban_reason}."
        try:
            await c.send_message(
                user_id,
                f"You are banned to use this bot for **{ban_duration}** day(s) for the reason __{ban_reason}__ \n\n**Message from the admin**"
            )
            ban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            ban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
        await db.ban_user(user_id, ban_duration, ban_reason)
        print(ban_log_text)
        await m.reply_text(
            ban_log_text,
            quote=True
        )
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occoured! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Bot.on_message(filters.private & filters.command("unban") & filters.user(BOT_OWNER))
async def unban(c, m):
    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to unban any user.\n\nUsage:\n\n`/unban user_id`\n\nEg: `/unban 1234567`\n This will unban user with id `1234567`.",
            quote=True
        )
        return
    try:
        user_id = int(m.command[1])
        unban_log_text = f"Unbanning user {user_id}"
        try:
            await c.send_message(
                user_id,
                f"Your ban was lifted!"
            )
            unban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            unban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
        await db.remove_ban(user_id)
        print(unban_log_text)
        await m.reply_text(
            unban_log_text,
            quote=True
        )
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occoured! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )

Bot.run()
