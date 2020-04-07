from __future__ import absolute_import
import json
from wtforms.validators import ValidationError
from .quick_validation import (
    UsernameFieldMixin,
    PasswordFieldMixin,
    MailAddressFieldMixin,
    IPv4AddressMixin,
    PortMixin,
    QuickForm
)
from typing import Optional, Dict, Any, Generic
import os
from ..models.user import User
from flask_script.commands import InvalidCommand, Command
from flask import current_app
from typing import Union, TypeVar
from flask_script.cli import prompt, prompt_choices, prompt_bool
from .constants import PAINTER_ENV_NAME, DEFAULT_TITLE, CONFIG_FILE_PATH_KEY, DEFAULT_PATH, MANAGER_TYPES_PARSE
import base64


ConvertType = TypeVar('Convert', str, int, bool, float)

class NewUserForm(
    QuickForm,
    UsernameFieldMixin,
    PasswordFieldMixin,
    MailAddressFieldMixin,
):

    def validate_mail_address(self, field) -> None:
        if User.query.filter_by(email=field.data).first() is not None:
            raise ValidationError('User with the mail address already exists')

    def validate_username(self, field) -> None:
        if User.query.filter_by(username=field.data).first() is not None:
            raise ValidationError('User with the username already exists')


class PortQuickForm(
    QuickForm,
    PortMixin
):
    pass


class IPv4QuickForm(
    QuickForm,
    IPv4AddressMixin
):
    pass


class DescriableCommand(Command):
    """
    simple command but with options to describe itself
    """
    def __init__(self, func=None,
                 description: Optional[str] = None,
                 help_text: Optional[str] = None):
        super().__init__(func)
        self.__description = description
        self.__help_text = help_text

    @property
    def description(self):
        desc = self.__description if self.__description is not None else ''
        return desc.strip()

    @property
    def help(self):
        help_text = self.__help_text if self.__help_text is not None else self.__description
        return help_text.strip()


def check_isfile(path: str,
                 not_exist_message: Optional[str] = None,
                 isdir_message: Optional[str] = None) -> Optional[str]:
    not_exist_message = not_exist_message if not_exist_message else 'Path {0} don\'t exists'
    isdir_message = isdir_message if isdir_message else 'Path {0} points to a directory'
    if not os.path.exists(path):
        return not_exist_message.format(path)
    elif os.path.isdir(path):
        return isdir_message.format(path)
    return None


def try_load_config(path: str) -> Dict[str, Any]:
    try:
        fp = open(path, 'rt')
        json_parsed = json.load(fp)
        fp.close()
    except Exception as e:
        raise InvalidCommand('Error on loading configuration json\n:'
                             '{0}'.format(e))
    return json_parsed


def try_save_config(obj: Any) -> Dict[str, Any]:
    try:
        fp = open(current_app[CONFIG_FILE_PATH_KEY], 'wt')
        json_parsed = json.dump(obj, fp)
        fp.close()
    except Exception as e:
        raise InvalidCommand('Error on saving configuration json\n:'
                             '{0}'.format(e))
    return json_parsed


def __load_configuration(config_path: str, title: str) -> Dict[str, Any]:
    json_parsed = try_load_config(config_path)
    if DEFAULT_TITLE not in json_parsed:
        raise InvalidCommand('Default Title i\'snt found in json file')
    default_configuration = json_parsed[DEFAULT_TITLE]
    if not isinstance(default_configuration, dict):
        raise InvalidCommand("default configuration matched value isn\'t a dict but:{0}"
                             .format(type(default_configuration)))
    # if title isnt None
    if title is not None:
        if title not in json_parsed:
            raise InvalidCommand('Title {0} isnt included in'.format(str(title)))
        app_configuration = json_parsed[title]
        if not isinstance(app_configuration, dict):
            raise InvalidCommand("value for title {0} isn\'t a dict but:{1}"
                                 .format(title, type(app_configuration)))
        app_configuration.update(default_configuration)
    else:
        app_configuration = default_configuration
    # checks for bytes, now bytes determine only if there is a \n in the end and then triple \r\r\r\r
    for key in app_configuration:
        val = app_configuration[key]
        if isinstance(val, str) and val.endswith('\n\r\r\r\r'):
            app_configuration[key] = base64.decodebytes(val[:-4].encode())
    return app_configuration


def load_configuration(config_path: str, title: Optional[str] = None) -> Dict[str, Any]:
    error_text = check_isfile(config_path)
    if error_text is not None:
        raise InvalidCommand(error_text)
    # read configuration
    configuration = __load_configuration(config_path, title)
    configuration[CONFIG_FILE_PATH_KEY] = config_path
    return configuration


def get_config_json() -> Dict[str, Any]:
    config_path = current_app.config[CONFIG_FILE_PATH_KEY]
    error_text = check_isfile(config_path)
    if error_text is not None:
        raise InvalidCommand(error_text)
    # validate the port and host
    # read file
    # try load
    return try_load_config(config_path)


def __get_absolute_if_relative(pth: str) -> str:
    return pth if os.path.isabs(pth) else os.path.abspath(pth)


def get_env_path():
    if PAINTER_ENV_NAME not in os.environ:
        os.environ[PAINTER_ENV_NAME] = DEFAULT_PATH
    return __get_absolute_if_relative(os.environ.get(PAINTER_ENV_NAME))


def set_env_path(path: str) -> None:
    os.environ[PAINTER_ENV_NAME] = path


def config_name_utility(name: str,
                        callback_for_change: bool = True,
                        no_default: bool = False) -> str:
    # first fixes the name
    real_name = name.upper().replace(' ','_')
    if real_name != name and callback_for_change:
        print('Changed Name to more appropriate:{0}'.format(name))
    if no_default and real_name == DEFAULT_TITLE:
        raise InvalidCommand("You enter the default title, the command cannot be used on the default "
                             "configuration option")
    return real_name


"""
    Parsing Staffs
"""


def parse_boolean() -> Optional[bool]:
    return prompt_bool('Enter a boolean value\n[VALUE]', default=None)


def parse_bytes() -> Optional[str]:
    val = prompt('Enter a Bytes values')
    return (base64.encodebytes(val)+'\r\r\r\r').decode() if val else None


def parse_type(convert_type:Generic[ConvertType]) -> Optional[ConvertType]:
    val = prompt('Enter a valid {0} value\n[VALUE]'.format(convert_type.__name__))
    while val:
        try:
            return convert_type(val)
        except TypeError:
            pass
        val = prompt('Enter a valid {0} value\n[VALUE]'.format(convert_type.__name__))
    return None


def parse_string() -> Optional[str]:
    val = prompt('Enter a string\n[VALUE]')
    return val if val else None


CONVERT_MAP = {
    bool: parse_boolean,
    int: lambda: parse_type(int),
    float: lambda: parse_type(float),
    bytes: lambda: parse_bytes(),
    str: parse_string
}


def parse_value() -> Optional[ConvertType]:
    parsed_type = prompt_choices('Select a type', MANAGER_TYPES_PARSE)
    if parsed_type is None:
        return None
    # else parse
    return CONVERT_MAP[parsed_type]()
