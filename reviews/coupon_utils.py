"""Shared coupon usage helpers."""
from bson import ObjectId


def user_has_used_coupon(coupon, user_id):
    """Common coupons can be reused on every exam purchase."""
    if getattr(coupon, "is_common", False):
        return False

    user_object_id = ObjectId(user_id) if ObjectId.is_valid(str(user_id)) else user_id
    user_id_str = str(user_object_id)
    for used_user_id in getattr(coupon, "used_by", None) or []:
        if str(used_user_id) == user_id_str:
            return True
    return False


def mark_coupon_used_by_user(coupon, user_id):
    """Record one-time use for user-specific coupons only."""
    if getattr(coupon, "is_common", False):
        return False

    if user_has_used_coupon(coupon, user_id):
        return False

    user_object_id = ObjectId(user_id) if ObjectId.is_valid(str(user_id)) else user_id
    if ObjectId.is_valid(user_object_id):
        coupon.used_by.append(ObjectId(user_object_id))
    else:
        coupon.used_by.append(user_object_id)
    return True
