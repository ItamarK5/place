from typing import Optional, Union, List

from flask import Flask

from painter.models.user import User, Role
from painter.others.constants import COLORS
from painter.others.constants import MINUTES_COOLDOWN


def draw_time(user: User) -> str:
    # https://stackoverflow.com/a/35643540
    if user.next_time == user.creation:
        return 'never'
    # else
    return (user.next_time - MINUTES_COOLDOWN).strftime(
        '%y-%m-%d %a %H:%M:%S.%f'
    )


def is_admin(user: User) -> bool:
    """
    :param user: a user
    :return: returns if the user is admin
    """
    return user.is_authenticated and user.role >= Role.admin


def class_ftr(classes: Optional[Union[str, List]], comma: Optional[str] = None) -> str:
    if classes is None:
        return ''
    if isinstance(classes, list):
        classes = ' '.join(classes)
    # if comma
    if comma:
        return f'class={comma}{classes}{comma}'
    return f" {classes}"


def color(color_idx: int) -> str:
    return COLORS[color_idx]


def add_filters(flask_app: Flask) -> None:
    flask_app.add_template_filter(draw_time, 'draw_time')
    flask_app.add_template_filter(is_admin, 'is_admin')
    flask_app.add_template_filter(class_ftr, 'class_ftr')
    flask_app.add_template_filter(color, 'color')
