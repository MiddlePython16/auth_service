from flask import Blueprint, make_response, redirect, request
from flask_jwt_extended import jwt_required

from core.settings import settings

billing_view = Blueprint('billing', __name__, template_folder='templates')


@billing_view.route('/billing', methods=['GET'])
@jwt_required()
def redirect_to_biling():
    response = make_response(redirect(settings.BILLING_URL))
    access_token_cookie = request.cookies.get('access_token_cookie', None)
    if access_token_cookie:
        response.set_cookie('access_token_cookie', access_token_cookie)
    return response
