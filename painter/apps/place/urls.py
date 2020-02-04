from flask import Blueprint, render_template, abort, send_from_directory
from os.path import join as path_join
from painter.constants import WEB_FOLDER
from flask_login import login_required

place_router = Blueprint('place', 'place',
                         static_folder=path_join(WEB_FOLDER, 'static'),
                         template_folder=path_join(WEB_FOLDER, 'templates'))


@place_router.route('/place', methods=('GET',))
@login_required
def place():
    return render_template('place.html')
