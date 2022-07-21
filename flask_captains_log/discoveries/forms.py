from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
    validators,
)


class DiscoveryForm(FlaskForm):
    """WTForm class to log or edit discoveries"""

    description = TextAreaField(
        "Describe what you see:",
        [validators.DataRequired()],
        render_kw={"rows": 6, "autofocus": True},
    )
    submit = SubmitField("Log and Continue")


class PlanetNameForm(FlaskForm):
    """WTForm class to give a name to a planet after exploring it or rename it from the archive"""

    name = StringField(
        validators=[validators.DataRequired(), validators.Length(max=30)],
        render_kw={"autofocus": True, "onFocus": "this.select()"},
    )
    submit = SubmitField("Name Planet")
