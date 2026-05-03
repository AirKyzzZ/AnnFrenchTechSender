"""
Tests d'integration - Verification des interactions entre modules.

Contrairement aux tests unitaires qui testent chaque classe isolement,
les tests d'integration verifient que les modules fonctionnent ensemble :
  - Inscription → Connexion → Creation de profil → Sauvegarde/Chargement
  - Envoi → Enregistrement historique → Detection de doublon
  - Blacklist + Historique = double filtrage des URLs

Ces tests simulent un parcours utilisateur complet sans interface graphique.
"""

import csv
import pytest
from app.data.database import Database
from app.data.auth_manager import AuthManager
from app.data.profile_manager import ProfileManager
from app.data.history_manager import HistoryManager
from app.data.blacklist_manager import BlacklistManager
from app.data.config_manager import ConfigManager
from app.data.models import UserProfile, Settings


@pytest.fixture
def db(tmp_path):
    """Base de donnees temporaire partagee par tous les tests."""
    database = Database(str(tmp_path / "integration.db"))
    yield database
    database.fermer()


# ============================================================
# Test 1 : Parcours complet inscription → profil
# ============================================================

class TestParcoursAuthentificationProfil:
    """
    Simule le parcours : inscription → connexion → profil.
    Verifie que tous les modules communiquent correctement.
    """

    def test_inscription_connexion_profil(self, db):
        """Un utilisateur peut s'inscrire, se connecter, et gerer son profil."""
        auth = AuthManager(db)

        # Etape 1 : Inscription
        succes, msg = auth.inscrire("maxime", "monmdp123")
        assert succes is True

        # Etape 2 : Connexion
        succes, user_id, msg = auth.connecter("maxime", "monmdp123")
        assert succes is True
        assert user_id is not None

        # Etape 3 : Creer et sauvegarder un profil
        pm = ProfileManager(db, user_id)
        profile = UserProfile(
            nom="Mansiet", prenom="Maxime",
            email="max@epsi.fr", telephone="0600000000",
            objet="Demande de stage", message="Bonjour, je cherche un stage..."
        )
        pm.save(profile)

        # Etape 4 : Recharger le profil et verifier
        loaded = pm.load()
        assert loaded.nom == "Mansiet"
        assert loaded.email == "max@epsi.fr"
        assert loaded.message == "Bonjour, je cherche un stage..."
        assert loaded.is_valid() is True

    def test_profil_isole_par_utilisateur(self, db):
        """Chaque utilisateur a son propre profil independant."""
        auth = AuthManager(db)

        # Creer deux utilisateurs
        auth.inscrire("user1", "pass1234")
        auth.inscrire("user2", "pass5678")
        _, uid1, _ = auth.connecter("user1", "pass1234")
        _, uid2, _ = auth.connecter("user2", "pass5678")

        # Chacun sauvegarde un profil different
        pm1 = ProfileManager(db, uid1)
        pm2 = ProfileManager(db, uid2)

        pm1.save(UserProfile(nom="User1", prenom="A", email="u1@t.com",
                             telephone="01", objet="Stage", message="Msg1"))
        pm2.save(UserProfile(nom="User2", prenom="B", email="u2@t.com",
                             telephone="02", objet="Stage", message="Msg2"))

        # Chacun ne voit que son profil
        assert pm1.load().nom == "User1"
        assert pm2.load().nom == "User2"

    def test_mise_a_jour_profil(self, db):
        """La mise a jour d'un profil remplace les anciennes valeurs."""
        auth = AuthManager(db)
        auth.inscrire("maxime", "monmdp123")
        _, user_id, _ = auth.connecter("maxime", "monmdp123")

        pm = ProfileManager(db, user_id)

        # Premier profil
        pm.save(UserProfile(nom="Ancien", prenom="X", email="old@t.com",
                            telephone="01", objet="Old", message="Ancien msg"))
        assert pm.load().nom == "Ancien"

        # Mise a jour
        pm.save(UserProfile(nom="Nouveau", prenom="Y", email="new@t.com",
                            telephone="02", objet="New", message="Nouveau msg"))
        loaded = pm.load()
        assert loaded.nom == "Nouveau"
        assert loaded.email == "new@t.com"


# ============================================================
# Test 2 : Historique + filtrage des URLs
# ============================================================

class TestParcoursEnvoiHistorique:
    """
    Simule le parcours : envoi → historique → filtrage.
    Verifie que l'historique empeche les doublons.
    """

    def test_historique_filtre_urls_envoyees(self, db, tmp_path):
        """Les URLs deja envoyees avec succes sont filtrees."""
        auth = AuthManager(db)
        auth.inscrire("maxime", "monmdp123")
        _, user_id, _ = auth.connecter("maxime", "monmdp123")

        hm = HistoryManager(db, user_id)

        # Simuler des envois passes
        hm.enregistrer_envoi("https://ftb.com/organisations/org1", "succes")
        hm.enregistrer_envoi("https://ftb.com/organisations/org2", "echec")
        hm.enregistrer_envoi("https://ftb.com/organisations/org3", "succes")

        # Preparer une liste de 5 URLs (dont 2 deja envoyees avec succes)
        toutes_urls = [
            "https://ftb.com/organisations/org1",  # deja envoye
            "https://ftb.com/organisations/org2",  # echec → on peut retenter
            "https://ftb.com/organisations/org3",  # deja envoye
            "https://ftb.com/organisations/org4",  # nouveau
            "https://ftb.com/organisations/org5",  # nouveau
        ]

        # Filtrer avec l'historique
        urls_deja = hm.get_urls_envoyees()
        urls_a_envoyer = [u for u in toutes_urls if u not in urls_deja]

        # On attend 3 URLs (org2 en echec + org4 + org5)
        assert len(urls_a_envoyer) == 3
        assert "https://ftb.com/organisations/org2" in urls_a_envoyer
        assert "https://ftb.com/organisations/org4" in urls_a_envoyer
        assert "https://ftb.com/organisations/org5" in urls_a_envoyer

    def test_double_filtrage_blacklist_historique(self, db, tmp_path):
        """Le filtrage combine blacklist (NoSQL) + historique (SQL)."""
        auth = AuthManager(db)
        auth.inscrire("maxime", "monmdp123")
        _, user_id, _ = auth.connecter("maxime", "monmdp123")

        # Blacklist (fichier texte = NoSQL)
        bl = BlacklistManager(str(tmp_path / "blacklist.txt"))
        bl.add("https://ftb.com/organisations/org_blacklist")

        # Historique (SQLite = SQL)
        hm = HistoryManager(db, user_id)
        hm.enregistrer_envoi("https://ftb.com/organisations/org_deja_fait", "succes")

        # Creer un CSV de test
        csv_path = str(tmp_path / "urls.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["URL"])
            writer.writerow(["https://ftb.com/organisations/org_blacklist"])
            writer.writerow(["https://ftb.com/organisations/org_deja_fait"])
            writer.writerow(["https://ftb.com/organisations/org_nouveau"])

        # Charger et filtrer (reproduit la logique du sender_engine)
        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            next(reader)
            urls = [row[0] for row in reader if row and row[0] not in bl.as_set()]

        urls_deja = hm.get_urls_envoyees()
        urls_finales = [u for u in urls if u not in urls_deja]

        # Seule org_nouveau passe les 2 filtres
        assert len(urls_finales) == 1
        assert urls_finales[0] == "https://ftb.com/organisations/org_nouveau"


# ============================================================
# Test 3 : Configuration + persistence
# ============================================================

class TestParcoursConfiguration:
    """Verifie que la config (JSON/NoSQL) fonctionne avec le reste."""

    def test_config_et_blacklist_path(self, tmp_path):
        """Le chemin de la blacklist dans la config est respecte."""
        config_path = str(tmp_path / "config.json")
        bl_path = str(tmp_path / "custom_blacklist.txt")

        cm = ConfigManager(config_path)
        settings = Settings(blacklist_path=bl_path)
        cm.save(settings)

        # Recharger les settings
        loaded = cm.load()

        # Utiliser le chemin de la blacklist depuis les settings
        bl = BlacklistManager(loaded.blacklist_path)
        bl.add("https://example.com/org1")

        # Verifier que le bon fichier est utilise
        bl2 = BlacklistManager(bl_path)
        assert bl2.contains("https://example.com/org1")
