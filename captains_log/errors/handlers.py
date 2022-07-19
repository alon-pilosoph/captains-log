from flask import Blueprint, render_template

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(404)
def error_404(error):
    """View to render custom HTTP 404 page"""
    return render_template("errors/404.html"), 404


@errors.app_errorhandler(403)
def error_403(error):
    """View to render custom HTTP 403 page"""
    return render_template("errors/403.html"), 403


@errors.app_errorhandler(500)
def error_500(error):
    """View to render custom HTTP 500 page"""
    return render_template("errors/500.html"), 500
