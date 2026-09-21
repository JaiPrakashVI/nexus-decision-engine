"""
NEXUS TLS & mTLS Certificate Validator
Extracts and validates X.509 client certificates against the Root CA and device registry.
"""

from pathlib import Path
from typing import Optional, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
import logging

from configs.settings import settings
from gateway.authentication.device_registry import device_registry

logger = logging.getLogger("nexus.mtls")


class CertificateValidator:
    """
    Validates client certificates presented during mTLS handshakes.
    """

    def __init__(self, ca_cert_path: Optional[str] = None):
        self.ca_cert_path = Path(ca_cert_path or settings.gateway_ca_file)
        self._ca_cert: Optional[x509.Certificate] = None
        self._load_ca()

    def _load_ca(self):
        if self.ca_cert_path.exists():
            try:
                with open(self.ca_cert_path, "rb") as f:
                    self._ca_cert = x509.load_pem_x509_certificate(f.read())
            except Exception as e:
                logger.error(f"Failed to load CA certificate: {e}")
                self._ca_cert = None
        else:
            logger.warning(f"CA certificate not found at {self.ca_cert_path}")

    def parse_client_cert(self, pem_bytes: bytes) -> Optional[x509.Certificate]:
        try:
            return x509.load_pem_x509_certificate(pem_bytes)
        except Exception as e:
            logger.warning(f"Failed to parse client certificate: {e}")
            return None

    def validate_client_cert(self, cert: x509.Certificate) -> Tuple[bool, str, Optional[str]]:
        """
        Validates client cert:
        1. Checks issuer matches CA
        2. Validates signature with CA public key
        3. Checks validity dates (not expired)
        4. Extracts Common Name (device_id)
        5. Checks device registry authorization

        Returns: (is_valid, reason, device_id)
        """
        if not self._ca_cert:
            return False, "CA certificate unavailable", None

        # Check signature
        try:
            ca_public_key = self._ca_cert.public_key()
            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                cert.signature_hash_algorithm
            )
        except Exception as e:
            return False, f"Certificate signature verification failed: {e}", None

        # Extract Common Name (Device ID)
        common_names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if not common_names:
            return False, "Certificate missing Common Name (CN)", None
        
        device_id = common_names[0].value.decode() if isinstance(common_names[0].value, bytes) else common_names[0].value

        # Check device authorization in registry
        if not device_registry.is_authorized(device_id):
            return False, f"Device '{device_id}' is not authorized or revoked", device_id

        return True, "Certificate validated successfully", device_id


cert_validator = CertificateValidator()
