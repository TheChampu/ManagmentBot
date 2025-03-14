# <============================================== IMPORTS =========================================================>
from re import compile as compile_re
from re import escape
from shlex import split
from typing import List, Union

from pyrogram.enums import ChatMemberStatus as CMS
from pyrogram.enums import ChatType
from pyrogram.filters import create
from pyrogram.types import CallbackQuery, Message

from Champubot import BOT_ID, BOT_USERNAME, DEV_USERS, DRAGONS, OWNER_ID
from Champubot.utils.caching import ADMIN_CACHE, admin_cache_reload

# <=======================================================================================================>

SUDO_LEVEL = set(DRAGONS + DEV_USERS + [int(OWNER_ID)])
DEV_LEVEL = set(DEV_USERS + [int(OWNER_ID)])
PREFIX_HANDLER = ["!", "/", "$"]


# <================================================ FUNCTION =======================================================>
def command(
    commands: Union[str, List[str]],
    case_sensitive: bool = False,
    owner_cmd: bool = False,
    dev_cmd: bool = False,
    sudo_cmd: bool = False,
):
    async def func(flt, _, m: Message):
        if not m:
            return

        date = m.edit_date
        if date:
            return  # reaction

        if m.chat and m.chat.type == ChatType.CHANNEL:
            return

        if m and not m.from_user:
            return False

        if m.from_user.is_bot:
            return False

        if any([m.forward_from_chat, m.forward_from]):
            return False

        if owner_cmd and (m.from_user.id != OWNER_ID):
            # Only owner allowed to use this...!
            return False

        if dev_cmd and (m.from_user.id not in DEV_LEVEL):
            # Only devs allowed to use this...!
            return False

        if sudo_cmd and (m.from_user.id not in SUDO_LEVEL):
            # Only sudos and above allowed to use it
            return False

        text: str = m.text or m.caption
        if not text:
            return False
        regex = r"^[{prefix}](\w+)(@{bot_name})?(?: |$)(.*)".format(
            prefix="|".join(escape(x) for x in PREFIX_HANDLER),
            bot_name=BOT_USERNAME,
        )
        matches = compile_re(regex).search(text)
        if matches:
            m.command = [matches.group(1)]
            if matches.group(1) not in flt.commands:
                return False
            if matches.group(3) == "":
                return True
            try:
                for arg in split(matches.group(3)):
                    m.command.append(arg)
            except ValueError:
                pass
            return True
        return False

    commands = commands if isinstance(commands, list) else [commands]
    commands = {c if case_sensitive else c.lower() for c in commands}

    return create(
        func,
        "NormalCommandFilter",
        commands=commands,
        case_sensitive=case_sensitive,
    )


async def bot_admin_check_func(_, __, m: Message or CallbackQuery):
    """Check if bot is Admin or not."""

    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        return False

    # Telegram and GroupAnonyamousBot
    if m.sender_chat:
        return True

    try:
        admin_group = {i[0] for i in ADMIN_CACHE[m.chat.id]}
    except KeyError:
        admin_group = {
            i[0] for i in await admin_cache_reload(m, "custom_filter_update")
        }
    except ValueError as ef:
        # To make language selection work in private chat of user, i.e. PM
        if ("The chat_id" and "belongs to a user") in ef:
            return True

    if BOT_ID in admin_group:
        return True

    await m.reply_text(
        "I am not an admin to receive updates in this group; Mind Promoting?",
    )

    return False


async def admin_check_func(_, __, m: Message or CallbackQuery):
    """Check if user is Admin or not."""
    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        return False

    # Telegram and GroupAnonyamousBot
    if m.sender_chat:
        return True

    if not m.from_user:
        return False

    try:
        admin_group = {i[0] for i in ADMIN_CACHE[m.chat.id]}
    except KeyError:
        admin_group = {
            i[0] for i in await admin_cache_reload(m, "custom_filter_update")
        }
    except ValueError as ef:
        # To make language selection work in private chat of user, i.e. PM
        if ("The chat_id" and "belongs to a user") in ef:
            return True

    if m.from_user.id in admin_group:
        return True

    await m.reply_text(text="You cannot use an admin command!")

    return False


async def owner_check_func(_, __, m: Message or CallbackQuery):
    """Check if user is Owner or not."""
    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        return False

    if not m.from_user:
        return False

    user = await m.chat.get_member(m.from_user.id)

    if user.status == CMS.OWNER:
        status = True
    else:
        status = False
        if user.status == CMS.ADMINISTRATOR:
            msg = "You're an admin only, stay in your limits!"
        else:
            msg = "Do you think that you can execute owner commands?"
        await m.reply_text(msg)

    return status


async def restrict_check_func(_, __, m: Message or CallbackQuery):
    """Check if user can restrict users or not."""
    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        return False

    if not m.from_user:
        return False

    user = await m.chat.get_member(m.from_user.id)

    if (
        user
        and user.status in [CMS.ADMINISTRATOR, CMS.OWNER]
        and user.privileges.can_restrict_members
    ):
        status = True
    else:
        status = False
        await m.reply_text(text="You don't have permissions to restrict members!")

    return status


async def promote_check_func(_, __, m: Message or CallbackQuery):
    """Check if user can promote users or not."""
    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        return False

    if not m.from_user:
        return False

    user = await m.chat.get_member(m.from_user.id)

    if (
        user.status in [CMS.ADMINISTRATOR, CMS.OWNER]
        and user.privileges.can_promote_members
    ):
        status = True
    else:
        status = False
        await m.reply_text(text="You don't have permission to promote members!")

    return status


async def changeinfo_check_func(_, __, m):
    """Check if user can change info or not."""
    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        await m.reply_text("This command is made to be used in groups not in pm!")
        return False

    # Telegram and GroupAnonyamousBot
    if m.sender_chat:
        return True

    user = await m.chat.get_member(m.from_user.id)

    if (
        user.status in [CMS.ADMINISTRATOR, CMS.OWNER]
        and user.privileges.can_change_info
    ):
        status = True
    else:
        status = False
        await m.reply_text("You don't have: can_change_info permission!")

    return status


async def can_pin_message_func(_, __, m):
    """Check if user can change info or not."""
    if isinstance(m, CallbackQuery):
        m = m.message

    if m.chat.type not in [ChatType.SUPERGROUP, ChatType.GROUP]:
        await m.reply_text("This command is made to be used in groups not in pm!")
        return False

    # Telegram and GroupAnonyamousBot
    if m.sender_chat:
        return True

    # Bypass the bot devs, sudos and owner
    if m.from_user.id in SUDO_LEVEL:
        return True

    user = await m.chat.get_member(m.from_user.id)

    if (
        user.status in [CMS.ADMINISTRATOR, CMS.OWNER]
        and user.privileges.can_pin_messages
    ):
        status = True
    else:
        status = False
        await m.reply_text("You don't have: can_pin_messages permission!")

    return status


admin_filter = create(admin_check_func)
owner_filter = create(owner_check_func)
restrict_filter = create(restrict_check_func)
promote_filter = create(promote_check_func)
bot_admin_filter = create(bot_admin_check_func)
can_change_filter = create(changeinfo_check_func)
can_pin_filter = create(can_pin_message_func)
# <================================================ END =======================================================>
