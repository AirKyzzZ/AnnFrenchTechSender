"""
conftest.py - Configuration partagee des tests pytest.

Ce fichier est automatiquement charge par pytest au demarrage.
Il s'assure que le repertoire racine du projet est dans le sys.path,
ce qui permet aux tests d'importer les modules de l'application.
"""

import sys
import os

# Ajouter le repertoire racine du projet au path Python
# pour que les imports "from app.xxx import yyy" fonctionnent dans les tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
