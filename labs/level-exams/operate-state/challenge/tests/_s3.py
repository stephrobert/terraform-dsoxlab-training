"""Client S3 minimal, signé SigV4, pour le harnais de l'épreuve B.

Sans dépendance : boto3 n'est pas garanti sur le poste de l'apprenant, et le
harnais n'a besoin que de cinq opérations sur le bucket du state.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import re
import urllib.error
import urllib.request
from urllib.parse import quote, urlparse

REGION = "us-east-1"


class S3:
    def __init__(self, endpoint: str, bucket: str, cle_acces: str, cle_secrete: str) -> None:
        self.hote = urlparse(endpoint).netloc
        self.base = endpoint.rstrip("/")
        self.bucket = bucket
        self.ak = cle_acces
        self.sk = cle_secrete

    def _signer(self, cle: bytes, msg: str) -> bytes:
        return hmac.new(cle, msg.encode(), hashlib.sha256).digest()

    def _requete(self, methode: str, cle: str = "", requete: dict[str, str] | None = None,
                 corps: bytes = b"") -> tuple[int, bytes]:
        maintenant = datetime.datetime.now(datetime.timezone.utc)
        amz = maintenant.strftime("%Y%m%dT%H%M%SZ")
        jour = maintenant.strftime("%Y%m%d")
        chemin = "/" + self.bucket + ("/" + quote(cle, safe="/") if cle else "")
        q = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted((requete or {}).items()))
        h_corps = hashlib.sha256(corps).hexdigest()
        entetes = f"host:{self.hote}\nx-amz-content-sha256:{h_corps}\nx-amz-date:{amz}\n"
        signes = "host;x-amz-content-sha256;x-amz-date"
        canon = f"{methode}\n{chemin}\n{q}\n{entetes}\n{signes}\n{h_corps}"
        portee = f"{jour}/{REGION}/s3/aws4_request"
        a_signer = f"AWS4-HMAC-SHA256\n{amz}\n{portee}\n{hashlib.sha256(canon.encode()).hexdigest()}"
        k = self._signer(self._signer(self._signer(self._signer(("AWS4" + self.sk).encode(), jour), REGION), "s3"), "aws4_request")
        signature = hmac.new(k, a_signer.encode(), hashlib.sha256).hexdigest()
        url = self.base + chemin + (f"?{q}" if q else "")
        req = urllib.request.Request(url, data=corps or None, method=methode, headers={
            "x-amz-date": amz,
            "x-amz-content-sha256": h_corps,
            "Authorization": f"AWS4-HMAC-SHA256 Credential={self.ak}/{portee}, SignedHeaders={signes}, Signature={signature}",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as rep:
                return rep.status, rep.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def cles(self) -> list[str]:
        code, corps = self._requete("GET", requete={"list-type": "2"})
        assert code == 200, f"liste du bucket refusée ({code}) : {corps[:200]!r}"
        return re.findall(r"<Key>([^<]+)</Key>", corps.decode())

    def lire(self, cle: str) -> bytes:
        code, corps = self._requete("GET", cle)
        assert code == 200, f"lecture de {cle} refusée ({code})"
        return corps

    def ecrire(self, cle: str, corps: bytes) -> int:
        return self._requete("PUT", cle, corps=corps)[0]

    def supprimer(self, cle: str) -> int:
        return self._requete("DELETE", cle)[0]

    def versionnage_actif(self) -> bool:
        code, corps = self._requete("GET", requete={"versioning": ""})
        return code == 200 and b"<Status>Enabled</Status>" in corps

    def versions(self, cle: str) -> list[str]:
        code, corps = self._requete("GET", requete={"versions": "", "prefix": cle})
        if code != 200:
            return []
        return [v for k, v in re.findall(r"<Key>([^<]+)</Key>.*?<VersionId>([^<]+)</VersionId>", corps.decode(), re.S) if k == cle]

    def lire_version(self, cle: str, version: str) -> bytes | None:
        code, corps = self._requete("GET", cle, requete={"versionId": version})
        return corps if code == 200 else None
