from __future__ import annotations
from wtforms import *
from flask_wtf import FlaskForm
import re

class LoginForm(FlaskForm):
    username = StringField('username',
                           description='Your name, it must contain 5-15 characters and'
                                       ' contains only abc chars\\digits',
                           validators=[
                               validators.data_required(message='You must enter something'),
                               validators.regexp(r'^[\w\d]+$', re.I, 'Input must only contain abc characters'
                                                                     ' or digits'),
                               validators.length(5, 15, message='you have passed the length, pass name in length'
                                                                'between 5 to 15',)
                           ],
                           render_kw={
                               'data-toggle': 'tooltip',
                               'title': 'Your nickname',
                               'data-placement': 'top'
                           })


    password = PasswordField('password',
                           description='It must only contain 6-15 abc chars or digits',
                           validators=[
                               validators.data_required('You must enter something'),
                               validators.regexp(r'^[\w\d]+$', re.I, 'Input must only contain abc characters'
                                                                     ' or digits'),
                               validators.length(6, 15, message='you have passed the length, pass name in length'
                                                                'between 6 to 15')
                           ],
                           render_kw={
                               'data-toggle': 'tooltip',
                               'title': 'One password to control your account, so keep it safe',
                               'data-placement': 'bottom'
                           })

class RegisterForm(FlaskForm):
    username = StringField(
        'username',
        description='Your name, it must contain 5-15 characters and contains only abc chars\\digits',
        validators=[
            validators.data_required(message='You must enter something'),
            validators.regexp(r'^[\w\d]+$', re.I, 'Input must only contain abc characters or digits'),
            validators.length(5, 15, message='you have passed the length, pass name in length between 5 to 15',)
            ], render_kw={
                'data-toggle': 'tooltip',
                'title': 'Your nickname',
                'data-placement': 'top',
            })
            
    password = PasswordField(
        'password',
        description='It must only contain 6-15 abc chars or digits',
        validators=[
            validators.data_required('You must enter something'),
            validators.regexp(r'^[\w\d]+$', re.I, 'Input must only contain abc characters or digits'),
            validators.length(6, 15, message='you have passed the length, pass name in length between 6 to 15')
            ], render_kw={
                'data-toggle': 'tooltip',
                'title': 'One password to control your account, so keep it safe',
                'data-placement': 'bottom'
        })

    confirm = PasswordField(
        'confirm password',
        description='Your password againYou must re-enter your password, so we be really sure that know your password',
        validators=[
            validators.data_required('You must re-enter the same password'),
            validators.regexp(r'^[\w\d]+$', re.I, 'You must re-enter the same password'),
            validators.length(6, 15, message='You must re-enter the same password')
            ], render_kw={
                'data-toggle': 'tooltip',
                'title': 'You must re-enter your password, so we be really sure that know your password',
                'data-placement': 'bottom'
        })        