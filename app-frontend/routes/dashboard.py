"""
Routes du dashboard principal.
Affiche les produits et les utilisateurs récupérés via l'API Gateway.
"""
from flask import Blueprint, redirect, url_for, session, render_template, request, flash
from services import gateway

dashboard_bp = Blueprint("dashboard", __name__)

# Mapping icônes pour les types de produits
PRODUCT_ICONS = {
    "auto": ("auto", "🚗"),
    "habitation": ("habita", "🏠"),
}
DEFAULT_ICON = ("vie", "❤️")


def _get_product_icon(name):
    """Retourne la classe CSS et l'icône selon le type de produit."""
    name_lower = name.lower()
    for keyword, icon_data in PRODUCT_ICONS.items():
        if keyword in name_lower:
            return icon_data
    return DEFAULT_ICON


@dashboard_bp.route("/")
def home():
    """
    Page principale du dashboard.
    Affiche les stats, les produits et les utilisateurs.
    Requiert une session active (login via Keycloak).
    """
    if "username" not in session:
        return redirect(url_for("auth.login"))

    username = session["username"]

    # Récupération des données via l'API Gateway
    products = gateway.get_products()
    users = gateway.get_users()

    # Ajout des icônes aux produits pour le template
    for product in products:
        css_class, icon = _get_product_icon(product.get("name", ""))
        product["icon_class"] = css_class
        product["icon"] = icon

    return render_template(
        "dashboard.html",
        username=username,
        products=products,
        users=users,
    )
