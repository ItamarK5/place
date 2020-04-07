"""
Author: Itamar Kanne
the manager module decorates the app by command line parameter
the module is based of flask_script module
https://flask-script.readthedocs.io/en/latest/
"""
import subprocess
import sys
import click
from flask import current_app
from flask.cli import FlaskGroup
from flask_script import Manager, Server, Option, Command
from flask_script.cli import prompt_bool, prompt_choices, prompt
from flask_script.commands import InvalidCommand

from .app import create_app, datastore, sio, redis
from .models.role import Role
from .models.user import User
from .others.utils import (
    NewUserForm, PortQuickForm,
    IPv4QuickForm, get_config_json,
    CONFIG_FILE_PATH_KEY, try_save_config,
    DescriableCommand, config_name_utility,
    parse_value
)

CHECK_SERVICES_RESULT_FORMAT = '{:^8}{:^5}'


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    print(5)

manager = Manager(
    create_app,
    description='Social Painter CMD Starter,'
                'Its helps throught'
)
manager.add_option('--c', '-config', dest='config_path', required=False)
manager.add_option('--D', '-default', dest='set_env', action='store_true', required=False)
manager.add_option('--t', '-title', dest='title', required=False)


class RunServer(Server):
    """
    source: https://github.com/miguelgrinberg/flack/blob/master/manage.py
    auther: miguelgrinberg
    The Start Server Command
    the function get the following parameters:
    host: the host to start the server
    port: the port to start the server
    note: I add a couple of changes to the command
    """

    help = description = 'Runs the server'

    def get_options(self):
        options = (
            Option('-h', '--host',
                   dest='host',
                   default=None,
                   help='host url of the server'),
            Option('-p', '--port',
                   dest='port',
                   type=int,
                   default=None,
                   help='host port of the server'),
            Option('-d', '--debug',
                   action='store_true',
                   dest='use_debugger',
                   help=('enable the Werkzeug debugger (DO NOT use in '
                         'production code)'),
                   default=self.use_debugger),  # True
            Option('-D', '--no-debug',
                   action='store_false',
                   dest='use_debugger',
                   help='disable the Werkzeug debugger',
                   default=self.use_debugger),  # False
            Option('-r', '--reload',
                   action='store_true',
                   dest='use_reloader',
                   help=('monitor Python files for changes (not 100%% safe '
                         'for production use)'),
                   default=self.use_reloader),  # True
            Option('-R', '--no-reload',
                   action='store_false',
                   dest='use_reloader',
                   help='do not monitor Python files for changes',
                   default=self.use_reloader),  # False
        )
        return options

    def __call__(self, app, host, port, use_debugger, use_reloader):
        """
        :param  host: host the ip to run the server
        :type:  host: int
        :param  port: port to listen on the ip
        :type   port: int
        :param  use_debugger: if to use debbugger while running the application
        :type   use_debugger: bool
        :param  use_reloader: if to use the reloader option of flask
        :type   use_reloader: bool
        :return: nothing
        override the default runserver command to start a Socket.IO server
        """
        host = host if host is not None else app.config.get('APP_HOST', '127.0.0.1')
        port = port if port is not None else app.config.get('APP_PORT', 8080)
        print(host, port)
        if use_debugger is None:
            use_debugger = app.debug
            if use_debugger is None:
                use_debugger = True
        if use_reloader is None:
            use_reloader = (not app.debug) or app.config.get('WERKZEUG_RUN_MAIN', None) == 'true'
        print(app.config)
        sio.run(
            app,
            host=host,
            port=port,
            debug=use_debugger,
            use_reloader=use_reloader,
            **self.server_options
        )


class CreateUser(Command):
    description = 'create a new user in the system'
    help = 'creates a new user'

    def get_options(self):
        return (
            Option('--n', '-name', '-username',
                   dest='username',
                   help='username of the new user'),
            Option('--p', '-password', '-pswd',
                   dest='password',
                   help='password of the new user'),
            Option('--m', '-mail', '-addr', dest='mail_address',
                   help='mail address of the new user'),
            Option('--r', '-role', dest='role',
                   help='Role of the new User'),
            Option('--a', '-admin', dest='role',
                   help='the users\'s role is setted to be admin'),
            Option('--u', '-user',
                   dest='role', default='user',
                   help='the user\'s role is a simple user'
                   ),
            Option('--s', '-superuser',
                   dest='role', default='superuser',
                   help='the user\'s role is a superuser, highest rank')
        )

    def run(self, username, password, mail_address, role):
        if username is None:
            username = prompt('enter a username address of the user\n[username]')
        if password is None:
            password = prompt('you forgeot entering a password, pless enter 1\nPassword: ')
        if mail_address is None:
            mail_address = prompt('enter a mail address of the user\nMail:')
        if role is None:
            role = prompt_choices(
                'You must pick a role, if not default is superuser\n',
                [
                    ('admin', 'admin'),
                    ('a', 'admin'),
                    ('user', 'common'),
                    ('u', 'common'),
                    ('c', 'common'),
                    ('common', 'common'),
                    ('superuser', 'superuser'),
                    ('s', 'superuser')
                ],
                'superuser'
            )
        role_matched = Role.get_member_or_none(role)
        if role_matched is None:
            raise InvalidCommand('Pless enter a valid role, not: {0}'.format(role))
        # check valid role
        form, is_valid = NewUserForm.fast_validation(
            username=username,
            password=password,
            mail_address=mail_address
        )
        if not is_valid:
            # to get first error
            for field in iter(form):
                for error in field.errors:
                    raise InvalidCommand('{0}: {1}'.format(field.name, error))
        # create user
        else:
            user = User(
                username=username,
                password=password,
                email=mail_address,
                role=role_matched
            )
            datastore.session.add(user)
            datastore.session.commit()
            print('user created successfully')


class CeleryWorker(Command):
    """Starts the celery worker."""
    name = 'celery'

    def run(self):
        ret = subprocess.call(
            ['venv/scripts/celery.exe', 'worker', '-A', 'painter.tasks.mail_worker.celery', '-P', 'eventlet']
        )
        sys.exit(ret)


# adding command
manager.add_command('celery', CeleryWorker)
manager.add_command("runserver", RunServer())
manager.add_command("create-user", CreateUser())


def create_db(drop_first=False):
    if drop_first and prompt_bool('Are you sure you want to drop the table'):
        datastore.drop_all()
    datastore.create_all()


create_db_command = DescriableCommand(
    create_db,
    'creates the database'
)
create_db_command.add_option(
    Option('--d', '-drop', dest='drop_first',
           action='store_true', default=False,
           help='Drops the current database before creation')
)
manager.add_command('create-db', create_db_command)


# drop database
def drop_db():
    if prompt_bool('Are you sure to drop the database'):
        datastore.drop_all()
        print('You should create a new superuser, see create-user command')


drop_database_command = DescriableCommand(drop_db, 'drops the database entirely')
manager.add_command('drop-db', drop_database_command)


def add_config(config_name=None, host=None, port=None):
    # config_name in save mode
    config_name = config_name_utility(config_name, no_default=True)
    # get file
    configuration = get_config_json()
    if config_name in configuration:
        raise InvalidCommand('Configure Option {0} already exists'.format(config_name))
    # else get host and port
    # if passed any arguments => didn't pass both None
    if host is not None or port is not None:
        is_host_valid = host is None or IPv4QuickForm.are_valid(address=host)
        is_port_valid = port is None or PortQuickForm.are_valid(port=port)
        if not (is_host_valid or is_port_valid):
            raise InvalidCommand('Invalid Host and Port:{0}:{1}'.format(host, port))
        elif not is_host_valid:
            raise InvalidCommand('Invalid Host: {0}'.format(host))
        elif not is_port_valid:
            raise InvalidCommand('Invalid Port: {0}'.format(port))
    # parse if neither is None
    if host is None:
        is_valid = IPv4QuickForm.are_valid(address=host)
        while not is_valid:
            # after first parse
            host = prompt('Pless enter a valid IPv4 Address\n[HOST]')
            print(len(host))
            form, is_valid = IPv4QuickForm.fast_validation(address=host)
            if not is_valid:
                form.error_print()
    # validate port
    if port is None:
        is_valid = isinstance(port, str) and port.isdigit() and PortQuickForm.are_valid(port=port)
        while not is_valid:
            # after first parse
            port = prompt('pless enter a valid Port [0-65536]\n[PORT]')
            if not port.isdigit():
                print('Port must be a number')
                # dont validate because it still as before, false
            else:
                # check form now it knows that port cannot be a number
                form, is_valid = PortQuickForm.fast_validation(port=int(port))
                if not is_valid:
                    form.error_print()
    # add the configure
    configuration[config_name] = {
        'APP_HOST': host,
        'APP_PORT': int(port)
    }
    # save configuration
    try_save_config(configuration, current_app.config.get(CONFIG_FILE_PATH_KEY))
    print('Configuration {0} Created'.format(config_name))
    print('if you want to add more configuration, use the parse command')


create_config_command = DescriableCommand(
    add_config,
    'Adds a new configuration option inside the used configuration file (JSON Format)'
)
create_config_command.add_option(
    Option('--h', '-host', dest='host', default=None, required=False,
           help="Host/The IP Address of the server, default 127.0.0.1 (localhost), if no app configuration exist"),
)
create_config_command.add_option(
    Option('--p', '-port', dest='port', default=None, required=False,
           help="Port the server listens to default is 8080 if no app configuration is passed")
)
create_config_command.add_option(
    Option('--n', '-config_name', dest='config_name',
           help="Port the server listens to default is 8080 if no app configuration is passed")
)
manager.add_command('add-config', create_config_command)


# Delete Configuration
def del_config(config_name=None):
    config_name = config_name_utility(config_name, True)
    # get file
    # the real deal
    configuration = get_config_json()
    if config_name is None:
        while config_name not in configuration:
            config_name = config_name_utility(
                prompt('Enter a configure name'),
                False
            )
    if config_name not in configuration:
        raise InvalidCommand("Error, Config Title")
    # remove it
    if prompt_bool('Are you sure you want to remove the {0} config_name?'.format(config_name)):
        configuration.pop(config_name)
        try_save_config(configuration)
    else:
        print('as your wish, I stop the task')


del_config_command = DescriableCommand(
    del_config,
    'Delete entire Configuration (title)'
)
del_config_command.add_option(Option(
    '--n', '-config_name', dest='config_name', required=None
))
manager.add_command('del-config', del_config_command)


def parse_config(config_name, only_create=None):
    only_create = only_create if only_create is not None else False
    config_name = config_name_utility(config_name)
    all_configuration = get_config_json()
    if config_name not in all_configuration:
        raise InvalidCommand('Title {0} not found'.format(config_name))
    config = all_configuration[config_name]
    key = prompt('Parsing changes to configuration')
    while key is not None:
        key = config_name_utility(key)
        if key in config and only_create:
            print('Key {0} already registered in the configuration {1}'.format(config_name, key))
        else:
            pass
            # get type
    pass


command_parse_config = DescriableCommand(
    parse_config,
    description='option to parse keys to a configuration title',
    help_text='option to parse keys to the configuration title'
)
command_parse_config.add_option(
    Option('--n', '-name',
           dest='config_name',
           help='config_name of the configuration to parse the changes to',
           required=True)
)
command_parse_config.add_option(
    Option(
        '--o', '-only-create',
        dest='only_create', action='store_true',
        help='prevent any changes to current values, only create new staff',
        required=False, default=None
    )
)
manager.add_command('parse', command_parse_config)


def clear_config_key(config_name):
    config_name = config_name_utility(config_name)
    configuration = get_config_json()
    if config_name not in configuration:
        raise InvalidCommand('Title {0} not found'
                             .format(config_name))
    else:
        var_config_name = config_name_utility(
            prompt(
                'Enter a key in configuration to delete',
                default=''),
            False
        )
        while var_config_name:
            if var_config_name not in configuration:
                print('Error: key {0} not in configuration'.format(var_config_name))
            configuration[config_name].pop(var_config_name)
    try_save_config(configuration)
    print('Completely clear config')


clear_config_command = DescriableCommand(
    clear_config_key,
    description='clear keys in configuration option'
)
clear_config_command.add_option(
    Option('--n', '-name', dest='config_name', help='name of configuration to change')
)
manager.add_command('clear', clear_config_command)


"""
 Check Service Command
"""


def check_services(all_flag=False, redis_flag=None):
    # if in the future I should add other flagsw
    # check if all of them are None
    # if all of them are None, check them all
    redis_flag = all_flag if redis_flag is None else redis_flag ^ all_flag
    print('Checks with redis')
    results = {}
    if redis_flag:
        # try with redis
        try:
            redis.ping()
            print('Successfully ping to redis')
            results['redis'] = True
        except ConnectionError as e:
            print('Error:{0}'.format(e))
            print('Error while connection to redis:')
    print('Results:')
    for (key, connected) in results.items():
        print(CHECK_SERVICES_RESULT_FORMAT.format(key, connected))


check_services_command = Command(check_services)
check_services_command.__dict__['description'] = 'check if services the app uses are active,' \
                                             'there are currently 1: redis'
check_services_command.add_option(Option(
    '--r', '-redis', dest='redis_flag', action='store_true', help='to check update with redis'
))
check_services_command.add_option(Option(
    '--R', '-Redis', dest='redis_flag', action='store_false', help='to not check update with redis'
))
check_services_command.add_option(Option(
    '--a', '-all', dest='all_flag', action='store_true', help='to check update with all'
))
manager.add_command('check-service', check_services_command)
