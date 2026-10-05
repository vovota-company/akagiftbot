from collections import Counter, defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from api.auth.models import UserProfile

from .models import (
    AssetBalance,
    AssetLedgerEntry,
    ReferralCommission,
    ReferralEvent,
    ReferralStats,
)


LEVELS = ("V1", "V2", "V3", "V4", "V5", "V6")


def get_direct_commission(level):
    return settings.REFERRAL_DIRECT_COMMISSIONS_USDT[level]


def calculate_level(
    direct_count,
    network_count,
    level_counts,
):
    """
    Calculate highest qualifying level.

    Level rules:

    V6:
        20+ direct
        3+ V5 leaders
        1500+ network

    V5:
        12+ direct
        3+ V4 leaders
        800+ network

    V4:
        8+ direct
        3+ V3 leaders
        300+ network

    V3:
        5+ direct
        3+ V2 leaders
        100+ network

    V2:
        3+ direct
        20+ network

    Otherwise V1.
    """

    if (
        direct_count >= 20
        and level_counts.get("V5", 0) >= 3
        and network_count >= 1500
    ):
        return "V6"

    if (
        direct_count >= 12
        and level_counts.get("V4", 0) >= 3
        and network_count >= 800
    ):
        return "V5"

    if (
        direct_count >= 8
        and level_counts.get("V3", 0) >= 3
        and network_count >= 300
    ):
        return "V4"

    if (
        direct_count >= 5
        and level_counts.get("V2", 0) >= 3
        and network_count >= 100
    ):
        return "V3"

    if (
        direct_count >= 3
        and network_count >= 20
    ):
        return "V2"

    return "V1"


def _build_tree():
    profiles = list(
        UserProfile.objects.select_related("user").all()
    )

    children = defaultdict(list)

    for profile in profiles:
        if profile.referred_by_id:
            children[profile.referred_by_id].append(profile)

    return profiles, children


def _calculate_tree_node(profile_id, children, visiting, cache):
    """
    Calculate one node after calculating all descendants.

    Returns:
        level,
        network_count,
        level_counts
    """

    if profile_id in visiting:
        raise ValueError(
            "Referral tree cycle detected."
        )

    if profile_id in cache:
        return cache[profile_id]

    visiting.add(profile_id)

    direct_children = children.get(profile_id, [])

    network_count = 0
    level_counts = Counter()

    for child in direct_children:
        (
            child_level,
            child_network_count,
            child_level_counts,
        ) = _calculate_tree_node(
            child.id,
            children,
            visiting,
            cache,
        )

        network_count += 1 + child_network_count
        level_counts.update(child_level_counts)

    direct_count = len(direct_children)

    level = calculate_level(
        direct_count=direct_count,
        network_count=network_count,
        level_counts=level_counts,
    )

    level_counts[level] += 1

    result = (
        level,
        network_count,
        level_counts,
    )

    cache[profile_id] = result
    visiting.remove(profile_id)

    return result


def rebuild_referral_stats():
    """
    Recalculate referral statistics for every user.

    This follows the business rule that previous-level leaders
    can exist anywhere in the user's downline.
    """

    profiles, children = _build_tree()

    cache = {}

    roots = [
        profile
        for profile in profiles
        if profile.referred_by_id is None
    ]

    for root in roots:
        _calculate_tree_node(
            root.id,
            children,
            set(),
            cache,
        )

    for profile in profiles:
        (
            level,
            network_count,
            level_counts,
        ) = cache.get(
            profile.id,
            ("V1", 0, Counter()),
        )

        direct_count = len(
            children.get(profile.id, [])
        )

        stats, _ = ReferralStats.objects.get_or_create(
            profile=profile,
        )

        stats.level = level
        stats.direct_count = direct_count
        stats.network_count = network_count

        stats.v2_leader_count = level_counts.get(
            "V2",
            0,
        )

        stats.v3_leader_count = level_counts.get(
            "V3",
            0,
        )

        stats.v4_leader_count = level_counts.get(
            "V4",
            0,
        )

        stats.v5_leader_count = level_counts.get(
            "V5",
            0,
        )

        stats.save(
            update_fields=[
                "level",
                "direct_count",
                "network_count",
                "v2_leader_count",
                "v3_leader_count",
                "v4_leader_count",
                "v5_leader_count",
                "updated_at",
            ]
        )


def get_upline(sponsor, max_generations=None):
    """
    Return the sponsor's parents.

    generation 1 = sponsor's parent
    generation 2 = parent's parent
    ...
    """

    if max_generations is None:
        max_generations = settings.REFERRAL_MAX_UPLINE_LEVELS

    current = sponsor.referred_by
    generation = 1

    while (
        current is not None
        and generation <= max_generations
    ):
        yield current, generation

        current = current.referred_by
        generation += 1


def _credit_commission(
    event,
    recipient,
    source_user,
    commission_type,
    generation,
    amount,
):
    """
    Credit the user's internal USDT asset balance and create
    the immutable ledger entry.

    Unique constraints prevent duplicate commissions.
    """

    commission, created = (
        ReferralCommission.objects.get_or_create(
            event=event,
            recipient=recipient,
            commission_type=commission_type,
            generation=generation,
            defaults={
                "source_user": source_user,
                "amount": amount,
                "currency": settings.REFERRAL_CURRENCY,
            },
        )
    )

    if not created:
        return commission

    balance, _ = AssetBalance.objects.select_for_update().get_or_create(
        profile=recipient,
    )

    balance.available_usdt += amount
    balance.save(
        update_fields=[
            "available_usdt",
            "updated_at",
        ]
    )

    if commission_type == ReferralCommission.DIRECT:
        entry_type = AssetLedgerEntry.REFERRAL_DIRECT
    else:
        entry_type = AssetLedgerEntry.REFERRAL_INDIRECT

    AssetLedgerEntry.objects.create(
        profile=recipient,
        direction=AssetLedgerEntry.CREDIT,
        entry_type=entry_type,
        amount=amount,
        balance_after=balance.available_usdt,
        currency=settings.REFERRAL_CURRENCY,
        referral_commission=commission,
        reference=str(event.event_id),
    )

    return commission


@transaction.atomic
def process_new_referral(new_user_profile_id):
    """
    Process a referral event.

    Steps:

    1. Verify new user has a sponsor.
    2. Create one immutable ReferralEvent.
    3. Recalculate the entire referral tree.
    4. Pay sponsor according to current level.
    5. Pay up to six uplines.
    6. Record every payment in the asset ledger.

    The ReferralEvent + unique commission constraints make
    this operation idempotent.
    """

    new_user = (
        UserProfile.objects
        .select_related("referred_by")
        .select_for_update()
        .get(pk=new_user_profile_id)
    )

    sponsor = new_user.referred_by

    if sponsor is None:
        return {
            "processed": False,
            "reason": "no_referral",
        }

    if sponsor.pk == new_user.pk:
        raise ValueError(
            "A user cannot refer themselves."
        )

    event, created = ReferralEvent.objects.get_or_create(
        new_user=new_user,
        defaults={
            "sponsor": sponsor,
        },
    )

    if not created:
        return {
            "processed": False,
            "reason": "already_processed",
            "event_id": str(event.event_id),
        }

    # Recalculate all levels before determining
    # the sponsor's commission.
    rebuild_referral_stats()

    sponsor_stats = ReferralStats.objects.get(
        profile=sponsor,
    )

    direct_amount = get_direct_commission(
        sponsor_stats.level
    )

    _credit_commission(
        event=event,
        recipient=sponsor,
        source_user=new_user,
        commission_type=ReferralCommission.DIRECT,
        generation=0,
        amount=direct_amount,
    )

    indirect_amount = (
        settings.REFERRAL_INDIRECT_COMMISSION_USDT
    )

    indirect_payments = 0

    for upline, generation in get_upline(
        sponsor,
        settings.REFERRAL_MAX_UPLINE_LEVELS,
    ):
        _credit_commission(
            event=event,
            recipient=upline,
            source_user=new_user,
            commission_type=ReferralCommission.INDIRECT,
            generation=generation,
            amount=indirect_amount,
        )

        indirect_payments += 1

    return {
        "processed": True,
        "event_id": str(event.event_id),
        "sponsor_id": sponsor.id,
        "sponsor_level": sponsor_stats.level,
        "direct_amount": str(direct_amount),
        "indirect_amount": str(indirect_amount),
        "indirect_payments": indirect_payments,
    }
