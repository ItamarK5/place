from datetime import datetime
from typing import Any, Dict, Callable
from flask_login import current_user
from .extensions import datastore
from flask_socketio import SocketIO, Namespace, ConnectionRefusedError, disconnect
from painter.backends import board, lock
from functools import wraps
from painter.models.role import Role
import json


# declaring socketio namespace names
PAINT_NAMESPACE = '/paint'
ADMIN_NAMESPACE = '/admin'
PROFILE_NAMESPACE = '/profile'
sio = SocketIO(logger=True)


def socket_io_authenticated_only(f: Callable[[Any], Any]) -> Callable[[Any], Any]:
    @wraps(f)
    def wrapped(*args, **kwargs) -> Any:
        print(f)
        if current_user.is_anonymous or not current_user.is_active:
            raise disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


def socket_io_role_required(role: Role) -> Callable[[Any], Any]:
    """
    :param role: the required role to pass
    :return: the socket.io view, but now only allows if the user is authenticated
    """
    def wrapped(f: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            if not current_user.has_required_status(role):
                disconnect()
            else:
                return f(*args, **kwargs)
        return socket_io_authenticated_only(wrapper)
    return wrapped


def task_set_board(x: int, y: int, color: int) -> None:
    """
    :param x: valid x coordinate
    :param y: valid y coordinate
    :param color: color of the pixel
    :return: nothing
    sets a pixel on the screen
    -- sets the pixel in the redis server
    -- brodcast to all watchers that the pixel has changed
    """
    board.set_at(x, y, color)
    sio.emit('set-board', (x, y, color), namespace=PAINT_NAMESPACE)


@sio.on('connect', PAINT_NAMESPACE)
@socket_io_authenticated_only
def connect():
    """
    :return: suppose to do thing, just reject any connection from users
    """
    pass


@sio.on('get-starter', PAINT_NAMESPACE)
@socket_io_authenticated_only
def get_start_data():
    return {
        'board': board.get_board(),
        'time': str(current_user.next_time),
        'lock': not lock.is_enabled()
    }


@sio.on('set-board', PAINT_NAMESPACE)
@socket_io_authenticated_only
def set_board(params: Any) -> str:
    """
    :param params: params given to the Dictionary
    :return: string represent the next time the user can update the canvas,
             or undefined if couldn't update the screen
    """
    # somehow logged out between requests
    try:
        current_time = datetime.utcnow()
        if current_user.next_time > current_time:
            return json.dumps({'code': 'time', 'status': str(current_user.next_time)})
        if not lock.is_enabled():
            return json.dumps({'code': 'lock', 'status': 'true'})
        # validating parameter
        if 'x' not in params or (not isinstance(params['x'], int)) or not (0 <= params['x'] < 1000):
            return 'undefined'
        if 'y' not in params or (not isinstance(params['y'], int)) or not (0 <= params['y'] < 1000):
            return 'undefined'
        if 'color' not in params or (not isinstance(params['color'], int)) or not (0 <= params['color'] < 16):
            return 'undefined'
        next_time = current_time
        current_user.next_time = next_time
        datastore.session.add(current_user)
        datastore.session.commit()
        x, y, clr = int(params['x']), int(params['y']), int(params['color'])
        sio.start_background_task(task_set_board, x=x, y=y, color=clr)
        # setting the board
        """
        if x % 2 == 0:
            board[y, x // 2] &= 0xF0
            board[y, x // 2] |= clr
        else:
            board[y, x // 2] &= 0x0F
            board[y, x // 2] |= clr << 4
        """
        #        board.set_at(x, y, color)
        return json.dumps({'code': 'time', 'value': str(next_time)})
    except Exception as e:
        print(e, e.args)
        return 'undefined'


"""
    Admin Namespace
"""


@sio.on('connect', ADMIN_NAMESPACE)
@socket_io_role_required(Role.admin)
def connect():
    pass


@sio.on('change-lock-state', ADMIN_NAMESPACE)
@socket_io_role_required(Role.admin)
def change_lock_state(new_state: Any):
    if not isinstance(new_state, bool):
        return {'success': False, 'response': 'Not A Valid Input'}
    # prevent collision
    if lock.set_switch(new_state):
        sio.emit('change-lock-state', new_state, namespace=PAINT_NAMESPACE)
        sio.emit('set-lock-state', new_state, namespace=ADMIN_NAMESPACE, include_self=False)
        return {'success': True, 'response': new_state}
    else:
        return {'success': True, 'response': new_state}