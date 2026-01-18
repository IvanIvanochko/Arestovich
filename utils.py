import time
import discord


def has_role(member: discord.Member, role_id: int) -> bool:
    return any(r.id == role_id for r in member.roles)


async def find_recent_mute_actor(
    guild: discord.Guild,
    target: discord.Member,
    window_sec: int = 30
):
    """
    Повертає user, який замутив target (server mute), якщо знайде в audit log.
    """
    now = time.time()

    async for entry in guild.audit_logs(
        limit=50,
        action=discord.AuditLogAction.member_update
    ):
        if not entry.target or entry.target.id != target.id:
            continue

        if now - entry.created_at.timestamp() > window_sec:
            continue

        before = entry.changes.before
        after = entry.changes.after

        before_mute = getattr(before, "mute", None)
        after_mute = getattr(after, "mute", None)

        # Дозволяємо (False або None) -> True
        if after_mute is True and (before_mute is False or before_mute is None):
            return entry.user

    return None
