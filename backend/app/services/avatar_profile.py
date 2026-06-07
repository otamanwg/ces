from sqlalchemy.orm import Session

from backend.app.models import Player, PlayerAvatar

BODY_PRESET_CODES = ("body_standard", "body_sturdy")
FACE_PRESET_CODES = tuple(f"face_{index:02d}" for index in range(1, 21))
SKIN_TONE_CODES = tuple(f"skin_{index:02d}" for index in range(1, 7))
HAIR_STYLE_CODES = (
    "hair_short_01",
    "hair_short_02",
    "hair_medium_01",
    "hair_medium_02",
    "hair_long_01",
    "hair_long_02",
    "hair_buzz_01",
    "hair_bald",
)
HAIR_COLOR_CODES = (
    "hair_black",
    "hair_brown",
    "hair_blond",
    "hair_auburn",
    "hair_gray",
    "hair_white",
)
OUTFIT_SLOT_OPTIONS = {
    "upper": ("upper_stock_jacket",),
    "lower": ("lower_stock_jeans",),
    "footwear": ("footwear_stock_sneakers",),
    "outerwear": (),
    "headwear": (),
    "accessory": (),
}
DEFAULT_OUTFIT = {
    "upper": "upper_stock_jacket",
    "lower": "lower_stock_jeans",
    "footwear": "footwear_stock_sneakers",
}
STOCK_FASHION_SCORES = {
    "upper_stock_jacket": 3,
    "lower_stock_jeans": 3,
    "footwear_stock_sneakers": 2,
}
ANIMATION_PROFILE_CODE = "humanoid_context_v1"


def validate_avatar_selection(selection: dict) -> str | None:
    fields = (
        ("body_preset_code", BODY_PRESET_CODES, "статури"),
        ("face_preset_code", FACE_PRESET_CODES, "обличчя"),
        ("skin_tone_code", SKIN_TONE_CODES, "тону шкіри"),
        ("hair_style_code", HAIR_STYLE_CODES, "зачіски"),
        ("hair_color_code", HAIR_COLOR_CODES, "кольору волосся"),
    )
    for field, allowed, label in fields:
        if selection.get(field) not in allowed:
            return f"Невідомий варіант {label}."
    return None


def create_player_avatar(db: Session, player: Player, selection: dict | None = None) -> PlayerAvatar:
    data = selection or {}
    avatar = PlayerAvatar(
        player_id=player.id,
        body_preset_code=data.get("body_preset_code", BODY_PRESET_CODES[0]),
        face_preset_code=data.get("face_preset_code", FACE_PRESET_CODES[0]),
        skin_tone_code=data.get("skin_tone_code", SKIN_TONE_CODES[2]),
        hair_style_code=data.get("hair_style_code", HAIR_STYLE_CODES[0]),
        hair_color_code=data.get("hair_color_code", HAIR_COLOR_CODES[1]),
        equipped_outfit=dict(DEFAULT_OUTFIT),
        animation_profile_code=ANIMATION_PROFILE_CODE,
    )
    db.add(avatar)
    return avatar


def get_or_create_player_avatar(db: Session, player: Player) -> PlayerAvatar:
    avatar = player.avatar
    if avatar is None:
        avatar = create_player_avatar(db, player)
        db.flush()
    return avatar


def build_avatar_snapshot(db: Session, player: Player) -> dict:
    avatar = get_or_create_player_avatar(db, player)
    equipped_outfit = dict(avatar.equipped_outfit or DEFAULT_OUTFIT)
    return {
        "body_preset_code": avatar.body_preset_code,
        "face_preset_code": avatar.face_preset_code,
        "skin_tone_code": avatar.skin_tone_code,
        "hair_style_code": avatar.hair_style_code,
        "hair_color_code": avatar.hair_color_code,
        "equipped_outfit": equipped_outfit,
        "animation_profile_code": avatar.animation_profile_code,
        "fashion_score": sum(STOCK_FASHION_SCORES.get(item_code, 0) for item_code in equipped_outfit.values()),
    }


def build_avatar_catalog() -> dict:
    return {
        "body_presets": list(BODY_PRESET_CODES),
        "face_presets": list(FACE_PRESET_CODES),
        "skin_tones": list(SKIN_TONE_CODES),
        "hair_styles": list(HAIR_STYLE_CODES),
        "hair_colors": list(HAIR_COLOR_CODES),
        "outfit_slots": {slot: list(options) for slot, options in OUTFIT_SLOT_OPTIONS.items()},
        "animation_profile_code": ANIMATION_PROFILE_CODE,
    }
