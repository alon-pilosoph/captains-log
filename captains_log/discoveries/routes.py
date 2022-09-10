from captains_log import db
from captains_log.discoveries.forms import (
    DiscoveryForm,
    PlanetNameForm,
)
from captains_log.models import Planet, Discovery
from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from random import randint

# Initialize Blueprint
discoveries = Blueprint("discoveries", __name__)


@discoveries.route("/explore", methods=["GET", "POST"])
@login_required
def explore():
    """View to present the user with a random planet to explore"""

    current_planet = current_user.current_planet
    current_discovery = current_user.current_discovery

    # Conditions to redirect the user to current stage of exploration
    # If there is already a planet being explored
    if current_planet is not None:
        # If current discovery isn't logged, redirect to that discovery page
        if current_discovery.description is None:
            return redirect(
                url_for(
                    "discoveries.discovery",
                    planet_id=current_planet.id,
                    discovery_number=current_discovery.number,
                )
            )
        # Otherwise, redirect to naming of planet
        else:
            return redirect(
                url_for("discoveries.name_planet", planet_id=current_planet.id)
            )

    # If a form was submitted, get the number of things to discover
    if request.method == "POST":
        things_to_discover = request.form["things_to_discover"]
        # Create a new planet
        planet = Planet(things_to_discover=things_to_discover, user_id=current_user.id)
        db.session.add(planet)
        db.session.commit()
        # Generate random priompt
        circumstances, thing_discovered = planet.generate_prompt()
        # Create the first discovery in the planet
        discovery = Discovery(
            number=1,
            circumstances=circumstances,
            thing_discovered=thing_discovered,
            description=None,
            planet_id=planet.id,
        )
        db.session.add(discovery)
        db.session.commit()
        # Update user's current planet and discovery
        current_user.current_planet_id = planet.id
        current_user.current_discovery_id = discovery.id
        db.session.commit()
        # Redirect to first discovery
        return redirect(
            url_for("discoveries.discovery", planet_id=planet.id, discovery_number=1)
        )

    # If page was reached by GET method, render page to choose planet to explore
    return render_template("explore.html", things_to_discover=randint(1, 6))


@discoveries.route(
    "/explore/<int:planet_id>/<int:discovery_number>", methods=["GET", "POST"]
)
@login_required
def discovery(planet_id, discovery_number):
    """View to log discoveries in current planet being explored"""

    current_planet = current_user.current_planet
    current_discovery = current_user.current_discovery

    # Validate route
    if (
        current_planet is None
        or planet_id != current_planet.id
        or discovery_number != current_discovery.number
        or current_discovery.description is not None
    ):
        abort(404)

    # Create WTForm to log the discovery
    form = DiscoveryForm()
    # If form validated, update discovery in db
    if form.validate_on_submit():
        current_discovery.description = form.description.data
        db.session.commit()
        # If the updated discovery was the last one in this planet, redirect to naming of planet
        if current_discovery.number == current_planet.things_to_discover:
            return redirect(
                url_for("discoveries.name_planet", planet_id=current_planet.id)
            )
        # Generate random prompt
        circumstances, thing_discovered = current_planet.generate_prompt()
        # After updating current discovery, create the next one
        discovery = Discovery(
            number=current_discovery.number + 1,
            circumstances=circumstances,
            thing_discovered=thing_discovered,
            description=None,
            planet_id=current_planet.id,
        )
        db.session.add(discovery)
        db.session.commit()
        # Update user's current discovery
        current_user.current_discovery_id = discovery.id
        db.session.commit()
        # Redirect to next discovery
        return redirect(
            url_for(
                "discoveries.discovery",
                planet_id=planet_id,
                discovery_number=discovery_number + 1,
            )
        )

    # If page was reached by GET method, render page to log current discovery
    return render_template(
        "discovery.html",
        discovery=current_discovery,
        planet=current_planet,
        section="discoveries.explore",
        form=form,
    )


@discoveries.route("/explore/<int:planet_id>/name", methods=["GET", "POST"])
@login_required
def name_planet(planet_id):
    """View to name planet after discovering everything on it"""

    current_planet = current_user.current_planet
    current_discovery = current_user.current_discovery

    # Validate route
    if planet_id != current_planet.id or current_discovery.description is None:
        abort(404)

    # Create WTForm to name the planet
    form = PlanetNameForm()
    # If form validated, update name in db
    if form.validate_on_submit():
        planet_id = current_planet.id
        current_planet.name = form.name.data
        # Reset current planet and current discovery
        current_user.current_planet_id = None
        current_user.current_discovery_id = None
        db.session.commit()
        flash("Planet archived successfully", "success")
        # Redirect to archive with newly discovered planet shown
        return redirect(url_for("discoveries.planet", planet_id=planet_id))
    # If page was reached by GET method, render page to name the planet
    elif request.method == "GET":
        # Populate form with default name from db
        form.name.data = current_planet.name

    return render_template("name.html", section="discoveries.explore", form=form)


@discoveries.route("/archive")
@login_required
def archive():
    """View to render archive page in order to present list of archived planets"""

    # Query db for all the planets associated with current user
    planets = (
        db.session.query(Planet)
        .join(Discovery)
        .filter(
            Planet.user_id == current_user.id,
            Discovery.number == 1,
            Discovery.description != None,
        )
    )

    # Pass planets to template
    return render_template("archive.html", planets=planets)


@discoveries.route("/archive/<int:planet_id>")
@login_required
def planet(planet_id):
    """View to list the discoveries of a planet"""

    # Validate that the planet exists and that the current user is authorized to view it
    planet = Planet.query.get_or_404(planet_id)
    if planet.explorer != current_user:
        abort(403)

    return render_template(
        "planet.html", planet=planet, current_planet_id=current_user.current_planet_id
    )


@discoveries.route("/archive/<int:planet_id>/rename", methods=["GET", "POST"])
@login_required
def rename_planet(planet_id):
    """View to rename archived planets. Planet id is passed as route variable."""

    # Query db for planet by id
    planet = Planet.query.get_or_404(planet_id)
    # Make sure planet is associated with current user
    if planet.explorer != current_user:
        abort(403)

    # Create WTForm to edit planet name
    form = PlanetNameForm()
    form.submit.label.text = "Rename"
    # If form validated, update planet name in db
    if form.validate_on_submit():
        planet.name = form.name.data
        db.session.commit()
        flash("Planet renamed successfully", "success")
        # Redirect to planet page in archive
        return redirect(url_for("discoveries.planet", planet_id=planet.id))
    # If page was reached by GET method, populate form with curernt name of planet
    elif request.method == "GET":
        form.name.data = planet.name

    # Render page with planet name form
    return render_template("name.html", section="discoveries.archive", form=form)


@discoveries.route("/archive/<int:planet_id>/delete", methods=["POST"])
@login_required
def delete_planet(planet_id):
    """View to delete archived planets. Planet id is passed as route variable.
    This page only accepts POST method from a form in the archive page."""

    # Query db for planet by id
    planet = Planet.query.get_or_404(planet_id)
    # Make sure planet is associated with current user
    if planet.explorer != current_user:
        abort(403)

    # Delete planet from db
    db.session.delete(planet)
    db.session.commit()
    flash("Planet deleted successfully", "success")
    # Redirect to archive
    return redirect(url_for("discoveries.archive"))


@discoveries.route(
    "/archive/<int:planet_id>/<int:discovery_number>/edit", methods=["GET", "POST"]
)
@login_required
def edit_discovery(planet_id, discovery_number):
    """View to edit archived discoveries. Planet id and discovery number are passed as route variables."""

    # Query db for discovery by planet id and discovery number
    discovery = Discovery.query.filter_by(
        planet_id=planet_id, number=discovery_number
    ).first()
    if discovery is None:
        abort(404)

    # Make sure discovery is associated with current user
    if discovery.planet.explorer != current_user:
        abort(403)

    # Create WTForm to edit discovery
    form = DiscoveryForm()
    form.submit.label.text = "Update"
    # If form validated, update discovery in db
    if form.validate_on_submit():
        discovery.description = form.description.data
        db.session.commit()
        flash("Your discovery has been updated.", "success")
        # Redirect to planet page in archive
        return redirect(url_for("discoveries.planet", planet_id=discovery.planet.id))
    # If page was reached by GET method, populate form with current description of discovery
    elif request.method == "GET":
        form.description.data = discovery.description

    # Render page with discovery form
    return render_template(
        "discovery.html",
        discovery=discovery,
        planet=discovery.planet,
        section="discoveries.archive",
        form=form,
    )
