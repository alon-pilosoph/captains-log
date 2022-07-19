import captains_log.constants as constants
from captains_log import db
from captains_log.discoveries.forms import (
    DiscoveryForm,
    PlanetNameForm,
)
from captains_log.models import Planet, Discovery
from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from random import randint, choice

# Initialize Blueprint
discoveries = Blueprint("discoveries", __name__)


@discoveries.route("/explore", methods=["GET", "POST"])
@login_required
def explore():
    """View to handle exploring.
    Each exploration consists of 3 stages: choose planet, log discoveries, name planet.
    User is redirected according to the current stage of exploration, as stored in db."""

    # If there is no planet currently explored
    if current_user.current_planet_id is None:
        # If a form was submitted, get the number of things to discover
        if request.method == "POST":
            things_to_discover = request.form["things_to_discover"]
            # Create a new planet
            planet = Planet(
                things_to_discover=things_to_discover, user_id=current_user.id
            )
            db.session.add(planet)
            db.session.commit()

            # Create the first discovery in the planet.
            # Prompt (circumstances, category and location) is randomly chosen.
            circumstances = choice(constants.CIRCUMSTANCES)
            thing_discovered = (
                f"{choice(constants.CATEGORIES)} {choice(constants.LOCATIONS)}"
            )
            discovery = Discovery(
                number=1,
                circumstances=circumstances,
                thing_discovered=thing_discovered,
                description=None,
                user_id=current_user.id,
                planet_id=planet.id,
            )
            db.session.add(discovery)
            db.session.commit()

            # Update user's current planet and discovery
            current_user.current_planet_id = planet.id
            current_user.current_discovery_id = discovery.id
            db.session.commit()

            return redirect(url_for("discoveries.explore"))

        # If page was reached by GET method, render page to choose planet to explore
        return render_template("explore.html", things_to_discover=randint(1, 6))
    # If there is a planet currently explored, store along with current discovery
    else:
        current_planet = current_user.current_planet
        current_discovery = current_user.current_discovery

        # If current discovery needs to be logged (i.e., needs a description)
        if current_discovery.description is None:
            # Create WTForm to log the discovery
            form = DiscoveryForm(request.form)
            # If form validated, update discovery in db
            if form.validate_on_submit():
                current_discovery.description = form.description.data
                db.session.commit()
                # If the updated discovery was the last one in this planet, redirect
                if current_discovery.number == current_planet.things_to_discover:
                    return redirect("explore")

                # After updating current discovery, create the next one
                circumstances = choice(constants.CIRCUMSTANCES)
                # Make sure the new discovery doesn't have the same prompt
                while True:
                    thing_discovered = (
                        f"{choice(constants.CATEGORIES)} {choice(constants.LOCATIONS)}"
                    )
                    if not Discovery.query.filter_by(
                        planet_id=current_planet.id,
                        thing_discovered=thing_discovered,
                    ).first():
                        break

                discovery = Discovery(
                    number=current_discovery.number + 1,
                    circumstances=circumstances,
                    thing_discovered=thing_discovered,
                    description=None,
                    user_id=current_user.id,
                    planet_id=current_planet.id,
                )
                db.session.add(discovery)
                db.session.commit()

                # Update user's current discovery
                current_user.current_discovery_id = discovery.id
                db.session.commit()
                return redirect(url_for("discoveries.explore"))

            # If page was reached by GET method, render page to log the current discovery
            return render_template(
                "discovery.html",
                discovery_number=current_discovery.number,
                planet=current_planet,
                prompt=f"{current_discovery.circumstances}: {current_discovery.thing_discovered}.",
                from_page="discoveries.explore",
                form=form,
            )
        # If current discovery was already logged (i.e., there are no more discoveries to log)
        else:
            # Create WTForm to name the planet
            form = PlanetNameForm(request.form)
            # If form validated, update name in db
            if form.validate_on_submit():
                planet_id = current_planet.id
                current_planet.name = form.name.data
                # Reset current planet and current discovery
                current_user.current_planet_id = None
                current_user.current_discovery_id = None
                db.session.commit()
                # Redirect to archive with newly discovered planet shown
                return redirect(url_for("discoveries.archive", show=planet_id))
            # If page was reached by GET method, render page to name the planet
            elif request.method == "GET":
                # Populate form with default name from db
                form.name.data = current_planet.name

            return render_template(
                "name.html", from_page="discoveries.explore", form=form
            )


@discoveries.route("/archive")
@login_required
def archive():
    """View to render archive page in order to present archived discoveries"""

    # Query db for all the planets associated with current user
    planets = Planet.query.filter_by(user_id=current_user.id).all()
    # Pass planets to template
    return render_template(
        "archive.html",
        planets=planets,
        current_planet_id=current_user.current_planet_id,
    )


@discoveries.route("/archive/<discovery_id>/edit", methods=["GET", "POST"])
@login_required
def edit_discovery(discovery_id):
    """View to edit archived discoveries. Discovery id is passed as route variable."""

    # Query db for discovery by id
    discovery = Discovery.query.get_or_404(discovery_id)
    # Make sure discovery is associated with current user
    if discovery.explorer != current_user:
        abort(403)
    # Create WTForm to edit discovery
    form = DiscoveryForm(request.form)
    form.submit.label.text = "Update"
    # If form validated, update discovery in db
    if form.validate_on_submit():
        discovery.description = form.description.data
        db.session.commit()
        flash("Your discovery has been updated.", "success")
        # Redirect to archive and show planet with updated discovery
        return redirect(url_for("discoveries.archive", show=discovery.planet.id))
    # If page was reached by GET method, populate form with current description of discovery
    elif request.method == "GET":
        form.description.data = discovery.description
    # Render page with discovery form
    return render_template(
        "discovery.html",
        discovery_number=discovery.number,
        planet=discovery.planet,
        prompt=f"{discovery.circumstances}: {discovery.thing_discovered}.",
        from_page="discoveries.archive",
        form=form,
    )


@discoveries.route("/archive/<planet_id>/rename", methods=["GET", "POST"])
@login_required
def rename_planet(planet_id):
    """View to rename archived planets. Planet id is passed as route variable."""

    # Query db for planet by id
    planet = Planet.query.get_or_404(planet_id)
    # Make sure planet is associated with current user
    if planet.explorer != current_user:
        abort(403)
    # Create WTForm to edit planet name
    form = PlanetNameForm(request.form)
    form.submit.label.text = "Rename"
    # If form validated, update planet name in db
    if form.validate_on_submit():
        planet.name = form.name.data
        db.session.commit()
        # Redirect to archive and show planet with updated name
        return redirect(url_for("discoveries.archive", show=planet.id))
    # If page was reached by GET method, populate form with curernt name of planet
    elif request.method == "GET":
        form.name.data = planet.name
    # Render page with planet name form
    return render_template("name.html", from_page="discoveries.archive", form=form)


@discoveries.route("/archive/<planet_id>/delete", methods=["POST"])
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
    flash(f"Planet {planet.name} deleted successfully", "success")
    # Redirect to archive
    return redirect(url_for("discoveries.archive"))
