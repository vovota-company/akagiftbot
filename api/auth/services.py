import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework.exceptions import AuthenticationFailed , ValidationError
from .models import UserProfile
from api.wallets.services import ensure_wallet_for_user


User = get_user_model()


def verify_google_id_token(raw_token: str):
    if not settings.GOOGLE_CLIENT_ID:
        raise AuthenticationFailed('GOOGLE_CLIENT_ID is not configured.')
    try:
        payload = id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        raise AuthenticationFailed('Invalid Google ID token.') from exc

    if payload.get('iss') not in ('accounts.google.com', 'https://accounts.google.com'):
        raise AuthenticationFailed('Invalid Google token issuer.')
    if not payload.get('email_verified'):
        raise AuthenticationFailed('Google email is not verified.')
    if not payload.get('email') or not payload.get('sub'):
        raise AuthenticationFailed('Google token has no usable identity.')
    return payload





@transaction.atomic
def login_or_create_from_google(payload, referred_by_code=None):
    email = payload["email"].strip().lower()
    sub = payload["sub"]

    user = User.objects.filter(email__iexact=email).first()

    if user is None:
        referred_by_profile = None

        if referred_by_code:
            referred_by_code = referred_by_code.strip().upper()

            referred_by_profile = (
                UserProfile.objects
                .select_for_update()
                .filter(referral_code=referred_by_code)
                .first()
            )

            if referred_by_profile is None:
                raise ValidationError({
                    "referred_by": "This referral code does not belong to an existing user."
                })

        user = User.objects.create_user(
            username=f"google_{secrets.token_urlsafe(12)}",
            email=email,
            first_name=payload.get("given_name", "")[:150],
            last_name=payload.get("family_name", "")[:150],
        )

        user.set_unusable_password()
        user.save(update_fields=["password"])

        profile = UserProfile.objects.create(
            user=user,
            google_sub=sub,
            referred_by=referred_by_profile,
            is_active=False,
        )

    else:
        changed = False

        if payload.get("given_name") and not user.first_name:
            user.first_name = payload["given_name"][:150]
            changed = True

        if payload.get("family_name") and not user.last_name:
            user.last_name = payload["family_name"][:150]
            changed = True

        if user.has_usable_password():
            user.set_unusable_password()
            changed = True

        if changed:
            user.save()

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"google_sub": sub},
        )

        if profile.google_sub != sub:
            raise AuthenticationFailed(
                "Google identity does not match the existing account."
            )

        # Make sure old profiles get a referral code.
        if not profile.referral_code:
            profile.save()

    wallet = ensure_wallet_for_user(user)

    return user, wallet

def tokens_for_user(user):
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)

    return str(refresh.access_token), str(refresh)
