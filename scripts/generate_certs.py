"""
NEXUS Cryptographic Certificate Generator
Generates local Root CA, Server Certificate (with SANs), and Client mTLS Certificates.
Also generates a rogue/untrusted CA and certificate for security failure testing.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ipaddress


def generate_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


def save_key(key: rsa.RSAPrivateKey, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )


def save_cert(cert: x509.Certificate, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def create_ca(common_name: str, key_path: Path, cert_path: Path):
    key = generate_private_key()
    save_key(key, key_path)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NEXUS Cyber-Physical Security"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    save_cert(cert, cert_path)
    return key, cert


def create_server_cert(
    common_name: str,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    key_path: Path,
    cert_path: Path,
    sans: list[str] = None
):
    key = generate_private_key()
    save_key(key, key_path)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NEXUS Infrastructure"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    san_list = [
        x509.DNSName("localhost"),
        x509.DNSName("gateway"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]
    if sans:
        for item in sans:
            try:
                ip = ipaddress.ip_address(item)
                san_list.append(x509.IPAddress(ip))
            except ValueError:
                san_list.append(x509.DNSName(item))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=730))
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    save_cert(cert, cert_path)
    return key, cert


def create_client_cert(
    common_name: str,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    key_path: Path,
    cert_path: Path
):
    key = generate_private_key()
    save_key(key, key_path)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NEXUS Telemetry Device"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=730))
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    save_cert(cert, cert_path)
    return key, cert


def main():
    certs_dir = Path("certs")
    certs_dir.mkdir(parents=True, exist_ok=True)
    print("Generating NEXUS Root CA...")
    ca_key, ca_cert = create_ca("NEXUS-Root-CA", certs_dir / "ca.key", certs_dir / "ca.crt")

    print("Generating Gateway Server Certificate...")
    create_server_cert(
        "nexus-gateway",
        ca_key,
        ca_cert,
        certs_dir / "gateway.key",
        certs_dir / "gateway.crt",
        sans=["localhost", "127.0.0.1", "gateway"]
    )

    print("Generating Authorized Device Client Certificate...")
    create_client_cert(
        "sensor_001",
        ca_key,
        ca_cert,
        certs_dir / "device_001.key",
        certs_dir / "device_001.crt"
    )

    print("Generating Rogue/Untrusted CA & Cert for failure testing...")
    rogue_key, rogue_cert = create_ca(
        "Rogue-Untrusted-CA",
        certs_dir / "rogue_ca.key",
        certs_dir / "rogue_ca.crt"
    )
    create_client_cert(
        "unauthorized_sensor",
        rogue_key,
        rogue_cert,
        certs_dir / "unauthorized.key",
        certs_dir / "unauthorized.crt"
    )

    print("Certificates successfully generated in certs/ directory.")


if __name__ == "__main__":
    main()
