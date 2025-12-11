import sys
import subprocess
import os

print("[CycloneDX] SBOM oluşturuluyor...")

req_path = "requirements.txt"

if not os.path.exists(req_path):
    print(f"HATA: {req_path} bulunamadı!")
    sys.exit(1)

try:
    subprocess.check_call([
        sys.executable, "-m", "cyclonedx_py", 
        "requirements", 
        "--output-format", "json", 
        "--outfile", "sbom.json",
        req_path
    ])
    print("[Başarılı] sbom.json ana dizine kaydedildi.")
except subprocess.CalledProcessError as e:
    print(f"HATA: SBOM üretimi başarısız. {e}")
    sys.exit(1)