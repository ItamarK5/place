from __future__ import annotations
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.fields.html5 import IntegerRangeField


class SettingForm(FlaskForm):
    x_start = IntegerRangeField(
        'X',
        validators=[
            validators.Optional(),
            validators.NumberRange(min=0, max=1000, message='value out of range')
        ],
    )
    y_start = IntegerRangeField(
        'Y',
        validators=[
            validators.Optional(),
            validators.NumberRange(min=0, max=1000, message='coord out of range')
        ],
    )
    scale_start = IntegerRangeField(
        'Scale',
        validators=[
            validators.Optional(),
            validators.NumberRange(min=0, max=1000, message='scale out of range')
        ],
    )
    colors = SelectField(
        'Color',
        choices=(
            (0, 'White'), (1, 'Black'), (2, 'Gray'), (3, 'Silver'),
            (4, 'Red'), (5, 'Pink'), (6, 'Brown'), (7, 'Orange'),
            (8, 'Olive'), (9, 'Yellow'), (10, 'Green'), (11, 'Lime'),
            (12, 'Blue'), (13, 'Aqua'), (14, 'Purple'), (15, 'Magenta'),
        )
    )