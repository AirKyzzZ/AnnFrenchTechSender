"""
models.py - Modeles de donnees de l'application

Ce module definit les structures de donnees utilisees dans toute l'application.
On utilise des dataclasses Python : c'est une facon declarative de creer des
classes qui stockent des donnees, sans ecrire manuellement __init__, __repr__, etc.

Pourquoi des dataclasses ?
  → Moins de code repetitif (boilerplate) qu'une classe normale
  → Typage explicite de chaque champ (lisible, IDE-friendly)
  → Methodes utilitaires generees automatiquement (__init__, __eq__, __repr__)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """
    Represente un utilisateur de l'application.

    Ce modele est utilise pour transporter les donnees utilisateur dans l'app.
    Le mot de passe n'est PAS stocke ici (il reste dans la base en tant que hash).
    """
    id: int = 0
    username: str = ""


@dataclass
class UserProfile:
    nom: str = ""
    prenom: str = ""
    email: str = ""
    telephone: str = ""
    objet: str = ""
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_valid(self) -> bool:
        return all([self.nom, self.prenom, self.email, self.objet, self.message])


@dataclass
class Settings:
    delay_min: float = 2.0
    delay_max: float = 5.0
    timeout_page: int = 30
    timeout_bouton: int = 240
    max_tentatives: int = 5
    headless: bool = True
    rotation_active: bool = False
    duree_session_minutes: int = 15
    pause_entre_sessions_minutes: int = 4
    csv_path: str = "urls_entreprises.csv"
    blacklist_path: str = "blacklist.txt"
    log_path: str = "candidature_logs.log"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SendingStats:
    total: int = 0
    envoyes: int = 0
    echecs: int = 0
    en_cours: int = 0
    temps_debut: Optional[str] = None
    temps_fin: Optional[str] = None
    echecs_urls: list = field(default_factory=list)

    @property
    def taux_reussite(self) -> float:
        traites = self.envoyes + self.echecs
        if traites == 0:
            return 0.0
        return (self.envoyes / traites) * 100

    @property
    def traites(self) -> int:
        return self.envoyes + self.echecs

    def to_dict(self) -> dict:
        d = asdict(self)
        d["taux_reussite"] = self.taux_reussite
        d["traites"] = self.traites
        return d
