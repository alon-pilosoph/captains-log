from flask import Blueprint, render_template

# Initialize Blueprint
main = Blueprint("main", __name__)


@main.route("/")
def index():
    """View to render index page"""
    return render_template("index.html")


@main.route("/about")
def about():
    """View to render about page"""
    return render_template("about.html")


@main.route("/music")
def music():
    """View to render music page"""
    return render_template("music.html")
