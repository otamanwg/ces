from hashlib import sha256


def hash_player_token(player_token: str) -> str:
    return sha256(player_token.encode("utf-8")).hexdigest()
