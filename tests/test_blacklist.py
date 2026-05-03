"""
Tests unitaires pour le gestionnaire de liste noire (blacklist_manager.py).

La blacklist est un fichier texte (1 URL par ligne) = approche NoSQL.
Ces tests verifient les operations CRUD sur ce fichier.
"""

import pytest
from app.data.blacklist_manager import BlacklistManager


@pytest.fixture
def blacklist(tmp_path):
    """Fixture : cree un BlacklistManager avec un fichier temporaire."""
    filepath = str(tmp_path / "blacklist.txt")
    return BlacklistManager(filepath)


class TestBlacklist:
    """Tests pour le BlacklistManager."""

    def test_liste_vide_par_defaut(self, blacklist):
        """La liste est vide quand le fichier n'existe pas encore."""
        assert blacklist.load() == []
        assert blacklist.count() == 0

    def test_ajout_url(self, blacklist):
        """On peut ajouter une URL a la blacklist."""
        result = blacklist.add("https://example.com/org1")
        assert result is True
        assert blacklist.count() == 1

    def test_ajout_doublon(self, blacklist):
        """Ajouter une URL deja presente retourne False."""
        blacklist.add("https://example.com/org1")
        result = blacklist.add("https://example.com/org1")
        assert result is False
        assert blacklist.count() == 1  # Pas de doublon

    def test_suppression_url(self, blacklist):
        """On peut supprimer une URL de la blacklist."""
        blacklist.add("https://example.com/org1")
        result = blacklist.remove("https://example.com/org1")
        assert result is True
        assert blacklist.count() == 0

    def test_suppression_url_inexistante(self, blacklist):
        """Supprimer une URL absente retourne False."""
        result = blacklist.remove("https://example.com/inexistante")
        assert result is False

    def test_contains(self, blacklist):
        """contains() verifie si une URL est dans la blacklist."""
        blacklist.add("https://example.com/org1")
        assert blacklist.contains("https://example.com/org1") is True
        assert blacklist.contains("https://example.com/org2") is False

    def test_as_set(self, blacklist):
        """as_set() retourne un set pour des recherches rapides."""
        blacklist.add("https://example.com/org1")
        blacklist.add("https://example.com/org2")
        result = blacklist.as_set()
        assert isinstance(result, set)
        assert len(result) == 2

    def test_persistance(self, tmp_path):
        """Les donnees sont persistees entre deux instances."""
        filepath = str(tmp_path / "blacklist.txt")

        # Premiere instance : ajouter des URLs
        bm1 = BlacklistManager(filepath)
        bm1.add("https://example.com/org1")
        bm1.add("https://example.com/org2")

        # Deuxieme instance : les URLs doivent etre retrouvees
        bm2 = BlacklistManager(filepath)
        assert bm2.count() == 2
        assert bm2.contains("https://example.com/org1")

    def test_urls_triees(self, blacklist):
        """Les URLs sont triees alphabetiquement dans le fichier."""
        blacklist.add("https://z.com")
        blacklist.add("https://a.com")
        urls = blacklist.load()
        assert urls[0] == "https://a.com"
        assert urls[1] == "https://z.com"
