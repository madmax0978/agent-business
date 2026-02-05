"""
Validateurs pour les montants financiers avec Decimal strict

Ce module garantit:
- Précision exacte avec Decimal (pas de float)
- Validation des limites (min/max)
- Détection des valeurs invalides (négatif, zéro, NaN)
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union


class ValidationError(ValueError):
    """Erreur de validation personnalisée pour les montants financiers"""
    pass


def validate_financial_amount(
    amount: Union[float, int, Decimal, str],
    min_value: float = 0.01,
    max_value: float = 150_000.0,  # Plafond PEA
    field_name: str = "Montant"
) -> Decimal:
    """
    Valide et convertit en Decimal un montant financier.

    Args:
        amount: Montant à valider (float, int, Decimal ou str)
        min_value: Valeur minimale autorisée (défaut: 0.01€ = 1 centime)
        max_value: Valeur maximale autorisée (défaut: 150 000€ = plafond PEA)
        field_name: Nom du champ pour les messages d'erreur

    Returns:
        Decimal: Montant validé avec 2 décimales

    Raises:
        ValidationError: Si le montant est invalide

    Examples:
        >>> validate_financial_amount(100.50)
        Decimal('100.50')

        >>> validate_financial_amount(-10)
        ValidationError: Montant doit être positif: -10

        >>> validate_financial_amount(200000)
        ValidationError: Montant trop grand: 200000.00€ (max: 150000.00€)
    """
    # Conversion en Decimal
    try:
        if isinstance(amount, Decimal):
            dec_amount = amount
        else:
            # Convertir en string pour éviter les erreurs de précision float
            dec_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValidationError(
            f"{field_name} invalide: '{amount}'. Doit être un nombre valide."
        )

    # Vérifier que ce n'est pas NaN ou Infinity
    if not dec_amount.is_finite():
        raise ValidationError(
            f"{field_name} invalide: '{amount}'. Doit être un nombre fini."
        )

    # Arrondir à 2 décimales (centimes)
    dec_amount = dec_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Validation min
    min_dec = Decimal(str(min_value))
    if dec_amount < min_dec:
        raise ValidationError(
            f"{field_name} trop petit: {dec_amount}€ (min: {min_dec}€)"
        )

    # Validation max
    max_dec = Decimal(str(max_value))
    if dec_amount > max_dec:
        raise ValidationError(
            f"{field_name} trop grand: {dec_amount}€ (max: {max_dec}€)"
        )

    return dec_amount


def validate_stock_quantity(
    quantity: Union[float, int, Decimal, str],
    min_quantity: float = 0.01,  # Fractional shares supportées
    max_quantity: float = 100_000.0,
    field_name: str = "Quantité"
) -> Decimal:
    """
    Valide et convertit en Decimal une quantité d'actions.

    Args:
        quantity: Quantité à valider
        min_quantity: Quantité minimale (défaut: 0.01 = fractional shares)
        max_quantity: Quantité maximale (défaut: 100 000 actions)
        field_name: Nom du champ pour les messages d'erreur

    Returns:
        Decimal: Quantité validée avec 2 décimales

    Raises:
        ValidationError: Si la quantité est invalide

    Examples:
        >>> validate_stock_quantity(10)
        Decimal('10.00')

        >>> validate_stock_quantity(0.5)
        Decimal('0.50')

        >>> validate_stock_quantity(-5)
        ValidationError: Quantité trop petite: -5.00 (min: 0.01)
    """
    try:
        if isinstance(quantity, Decimal):
            dec_quantity = quantity
        else:
            dec_quantity = Decimal(str(quantity))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(
            f"{field_name} invalide: '{quantity}'. Doit être un nombre valide."
        )

    # Vérifier que ce n'est pas NaN ou Infinity
    if not dec_quantity.is_finite():
        raise ValidationError(
            f"{field_name} invalide: '{quantity}'. Doit être un nombre fini."
        )

    # Arrondir à 2 décimales
    dec_quantity = dec_quantity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Validation min
    min_dec = Decimal(str(min_quantity))
    if dec_quantity < min_dec:
        raise ValidationError(
            f"{field_name} trop petite: {dec_quantity} (min: {min_dec})"
        )

    # Validation max
    max_dec = Decimal(str(max_quantity))
    if dec_quantity > max_dec:
        raise ValidationError(
            f"{field_name} trop grande: {dec_quantity} (max: {max_dec})"
        )

    return dec_quantity


def validate_stock_price(
    price: Union[float, int, Decimal, str],
    min_price: float = 0.01,
    max_price: float = 10_000.0,
    field_name: str = "Prix"
) -> Decimal:
    """
    Valide et convertit en Decimal un prix d'action.

    Args:
        price: Prix à valider
        min_price: Prix minimum (défaut: 0.01€)
        max_price: Prix maximum (défaut: 10 000€ par action)
        field_name: Nom du champ pour les messages d'erreur

    Returns:
        Decimal: Prix validé avec 2 décimales

    Raises:
        ValidationError: Si le prix est invalide

    Examples:
        >>> validate_stock_price(50.25)
        Decimal('50.25')

        >>> validate_stock_price(0)
        ValidationError: Prix trop petit: 0.00€ (min: 0.01€)
    """
    try:
        if isinstance(price, Decimal):
            dec_price = price
        else:
            dec_price = Decimal(str(price))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(
            f"{field_name} invalide: '{price}'. Doit être un nombre valide."
        )

    # Vérifier que ce n'est pas NaN ou Infinity
    if not dec_price.is_finite():
        raise ValidationError(
            f"{field_name} invalide: '{price}'. Doit être un nombre fini."
        )

    # Arrondir à 2 décimales
    dec_price = dec_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Validation min
    min_dec = Decimal(str(min_price))
    if dec_price < min_dec:
        raise ValidationError(
            f"{field_name} trop petit: {dec_price}€ (min: {min_dec}€)"
        )

    # Validation max
    max_dec = Decimal(str(max_price))
    if dec_price > max_dec:
        raise ValidationError(
            f"{field_name} trop grand: {dec_price}€ (max: {max_dec}€)"
        )

    return dec_price


# Limites par défaut pour référence
PEA_MAX_DEPOSIT = 150_000.0  # Plafond légal PEA
MIN_TRANSACTION_AMOUNT = 0.01  # 1 centime
MIN_STOCK_QUANTITY = 0.01  # Support fractional shares
MIN_STOCK_PRICE = 0.01  # Prix minimum 1 centime
MAX_STOCK_PRICE = 10_000.0  # Prix maximum raisonnable
