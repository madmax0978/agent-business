#!/bin/bash
# ==========================================
# Setup Docker Secrets - Agent PEA
# ==========================================
#
# Script pour créer les fichiers secrets Docker de manière sécurisée
#
# Usage:
#   ./scripts/setup_secrets.sh
#
# Options:
#   --from-env     Créer depuis les variables d'environnement actuelles
#   --interactive  Mode interactif (demande chaque secret)
#   --rotate      Régénérer tous les secrets (rotation)
#   --check       Vérifier l'état des secrets sans modification
#
# Exemples:
#   # Mode interactif (recommandé pour premier déploiement)
#   ./scripts/setup_secrets.sh --interactive
#
#   # Depuis .env existant
#   source .env && ./scripts/setup_secrets.sh --from-env
#
#   # Vérification
#   ./scripts/setup_secrets.sh --check
#
# ==========================================

set -e  # Exit on error

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire des secrets
SECRETS_DIR="./secrets"

# Liste des secrets requis
REQUIRED_SECRETS=(
    "telegram_bot_token"
    "anthropic_api_key"
    "openai_api_key"
    "newsapi_key"
    "jwt_secret_key"
    "api_password"
)

# Mapping entre noms de fichiers et variables d'environnement
declare -A SECRET_ENV_MAPPING=(
    ["telegram_bot_token"]="TELEGRAM_BOT_TOKEN"
    ["anthropic_api_key"]="ANTHROPIC_API_KEY"
    ["openai_api_key"]="OPENAI_API_KEY"
    ["newsapi_key"]="NEWSAPI_KEY"
    ["jwt_secret_key"]="JWT_SECRET_KEY"
    ["api_password"]="API_PASSWORD"
)

# Descriptions pour chaque secret
declare -A SECRET_DESCRIPTIONS=(
    ["telegram_bot_token"]="Token du bot Telegram (format: 123456789:ABC...)"
    ["anthropic_api_key"]="Clé API Anthropic Claude (format: sk-ant-...)"
    ["openai_api_key"]="Clé API OpenAI (format: sk-...)"
    ["newsapi_key"]="Clé API NewsAPI"
    ["jwt_secret_key"]="Clé secrète JWT (min 32 caractères)"
    ["api_password"]="Mot de passe admin API (min 8 caractères)"
)

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  🔐 Setup Docker Secrets - Agent PEA${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Créer le répertoire des secrets
create_secrets_directory() {
    if [ ! -d "$SECRETS_DIR" ]; then
        mkdir -p "$SECRETS_DIR"
        print_success "Répertoire secrets/ créé"
    else
        print_info "Répertoire secrets/ existe déjà"
    fi
}

# Générer une clé aléatoire sécurisée
generate_random_secret() {
    local length=$1
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Vérifier le format d'un secret
validate_secret_format() {
    local name=$1
    local value=$2

    case "$name" in
        "telegram_bot_token")
            if [[ ! "$value" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
                return 1
            fi
            ;;
        "anthropic_api_key")
            if [[ ! "$value" =~ ^sk-ant- ]]; then
                return 1
            fi
            ;;
        "openai_api_key")
            if [[ ! "$value" =~ ^sk- ]]; then
                return 1
            fi
            ;;
        "jwt_secret_key")
            if [ ${#value} -lt 32 ]; then
                return 1
            fi
            ;;
        "api_password")
            if [ ${#value} -lt 8 ]; then
                return 1
            fi
            ;;
    esac
    return 0
}

# Créer un fichier secret avec permissions sécurisées
create_secret_file() {
    local name=$1
    local value=$2
    local file_path="$SECRETS_DIR/${name}.txt"

    # Créer le fichier
    echo -n "$value" > "$file_path"

    # Permissions sécurisées (600 = rw-------)
    chmod 600 "$file_path"

    print_success "Secret '$name' créé avec permissions 600"
}

# Vérifier l'état des secrets
check_secrets_status() {
    print_info "État des secrets:"
    echo

    local all_ok=true

    for secret in "${REQUIRED_SECRETS[@]}"; do
        local file_path="$SECRETS_DIR/${secret}.txt"

        if [ -f "$file_path" ]; then
            # Vérifier les permissions
            local perms=$(stat -f "%Lp" "$file_path" 2>/dev/null || stat -c "%a" "$file_path" 2>/dev/null)

            if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
                # Masquer la valeur pour l'affichage
                local value=$(cat "$file_path")
                local masked="${value:0:4}***"
                print_success "$secret: $masked (permissions: $perms)"
            else
                print_warning "$secret: existe mais permissions incorrectes ($perms, devrait être 600)"
                all_ok=false
            fi
        else
            print_error "$secret: MANQUANT"
            all_ok=false
        fi
    done

    echo
    if [ "$all_ok" = true ]; then
        print_success "Tous les secrets sont configurés correctement ✓"
        return 0
    else
        print_error "Certains secrets sont manquants ou mal configurés"
        return 1
    fi
}

# Mode interactif
setup_interactive() {
    print_info "Mode interactif - Configuration des secrets"
    echo

    for secret in "${REQUIRED_SECRETS[@]}"; do
        local file_path="$SECRETS_DIR/${secret}.txt"
        local description="${SECRET_DESCRIPTIONS[$secret]}"

        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Secret:${NC} $secret"
        echo -e "${YELLOW}Description:${NC} $description"

        # Vérifier si le secret existe déjà
        if [ -f "$file_path" ]; then
            local existing_value=$(cat "$file_path")
            local masked="${existing_value:0:4}***"
            print_warning "Valeur actuelle: $masked"
            echo
            read -p "Voulez-vous le remplacer? (o/N): " replace
            if [[ ! "$replace" =~ ^[oO]$ ]]; then
                print_info "Conservé"
                echo
                continue
            fi
        fi

        # Proposer génération automatique pour certains secrets
        if [ "$secret" = "jwt_secret_key" ] || [ "$secret" = "api_password" ]; then
            read -p "Générer automatiquement? (O/n): " auto_generate
            if [[ ! "$auto_generate" =~ ^[nN]$ ]]; then
                local length=64
                if [ "$secret" = "api_password" ]; then
                    length=16
                fi
                local value=$(generate_random_secret "$length")
                print_success "Secret généré: ${value:0:8}***"
                create_secret_file "$secret" "$value"
                echo
                continue
            fi
        fi

        # Demander la valeur
        while true; do
            read -sp "Entrez la valeur (vide pour passer): " value
            echo

            if [ -z "$value" ]; then
                print_warning "Passé"
                break
            fi

            # Valider le format
            if validate_secret_format "$secret" "$value"; then
                create_secret_file "$secret" "$value"
                break
            else
                print_error "Format invalide. Réessayez."
            fi
        done
        echo
    done
}

# Mode depuis variables d'environnement
setup_from_env() {
    print_info "Mode depuis variables d'environnement"
    echo

    local created_count=0
    local skipped_count=0

    for secret in "${REQUIRED_SECRETS[@]}"; do
        local env_var="${SECRET_ENV_MAPPING[$secret]}"
        local value="${!env_var}"

        if [ -z "$value" ]; then
            print_warning "$secret: Variable $env_var non définie, passé"
            ((skipped_count++))
            continue
        fi

        # Valider le format
        if ! validate_secret_format "$secret" "$value"; then
            print_error "$secret: Format invalide pour $env_var, passé"
            ((skipped_count++))
            continue
        fi

        create_secret_file "$secret" "$value"
        ((created_count++))
    done

    echo
    print_success "$created_count secrets créés, $skipped_count passés"
}

# Rotation des secrets (régénération)
rotate_secrets() {
    print_warning "ROTATION DES SECRETS"
    echo
    print_info "Cette opération va régénérer jwt_secret_key et api_password"
    print_warning "Les autres secrets (API keys) doivent être rotés manuellement"
    echo

    read -p "Continuer? (o/N): " confirm
    if [[ ! "$confirm" =~ ^[oO]$ ]]; then
        print_info "Annulé"
        exit 0
    fi

    # Régénérer jwt_secret_key
    print_info "Régénération de jwt_secret_key..."
    local jwt_secret=$(generate_random_secret 64)
    create_secret_file "jwt_secret_key" "$jwt_secret"

    # Régénérer api_password
    print_info "Régénération de api_password..."
    local api_password=$(generate_random_secret 16)
    create_secret_file "api_password" "$api_password"
    print_success "Nouveau mot de passe API: $api_password"

    echo
    print_success "Rotation des secrets terminée"
    print_warning "IMPORTANT: Redémarrez les services Docker pour appliquer les changements"
    print_info "  docker-compose -f docker-compose.prod.yml restart"
}

# ==========================================
# MAIN
# ==========================================

main() {
    print_header

    # Parser les arguments
    local mode="interactive"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --from-env)
                mode="from-env"
                shift
                ;;
            --interactive)
                mode="interactive"
                shift
                ;;
            --rotate)
                mode="rotate"
                shift
                ;;
            --check)
                mode="check"
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --from-env      Créer depuis les variables d'environnement"
                echo "  --interactive   Mode interactif (défaut)"
                echo "  --rotate        Rotation des secrets"
                echo "  --check         Vérifier l'état des secrets"
                echo "  -h, --help      Afficher cette aide"
                exit 0
                ;;
            *)
                print_error "Option inconnue: $1"
                exit 1
                ;;
        esac
    done

    # Créer le répertoire des secrets
    create_secrets_directory

    # Exécuter le mode approprié
    case $mode in
        "check")
            check_secrets_status
            ;;
        "interactive")
            setup_interactive
            echo
            check_secrets_status
            ;;
        "from-env")
            setup_from_env
            echo
            check_secrets_status
            ;;
        "rotate")
            rotate_secrets
            echo
            check_secrets_status
            ;;
    esac

    echo
    print_info "Prochaines étapes:"
    echo "  1. Vérifier les secrets: ./scripts/setup_secrets.sh --check"
    echo "  2. Démarrer en production: docker-compose -f docker-compose.prod.yml up -d --build"
    echo "  3. Vérifier les logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo
}

# Exécuter le script
main "$@"
