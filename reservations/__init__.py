from flask import Blueprint, redirect
from .sync import run as run_sync

reservations_bp = Blueprint("reservations", __name__)


@reservations_bp.route("/sync")
def sync():
    run_sync()
    return redirect("/")
