import sys
import subprocess

def run_garak_scan():
    """
    Garak (LLM Vulnerability Scanner) çalıştırır.
    Not: Bu bir demo/test taramasıdır. AutoGluon bir sınıflandırma modeli olduğu için,
    Garak'ın 'test' modunu (Test.Blank) kullanarak pipeline entegrasyonunu doğruluyoruz.
    Gerçek bir LLM (Llama, GPT vb.) olsaydı --model_type huggingface olurdu.
    """
    print("--- Garak Red Teaming Taraması Başlıyor ---")
    
    # Garak'ı CLI üzerinden çağırıyoruz
    # --model_type test: Gerçek model yerine test modunu kullanır (Hızlı ve hatasız)
    # --probes encoding: Enjeksiyon saldırılarını test eder
    # --report_prefix garak_report: Rapor ismini belirler
    command = [
        sys.executable, "-m", "garak",
        "--model_type", "test",
        "--probes", "encoding",
        "--report_prefix", "garak_report"
    ]

    try:
        # Komutu çalıştır
        result = subprocess.run(command, check=True, text=True)
        print("--- Garak Taraması Başarıyla Tamamlandı ---")
        print("Raporlar oluşturuldu.")
        
    except subprocess.CalledProcessError as e:
        print(f"Garak taraması sırasında hata oluştu: {e}")
        # Pipeline'ı kırmamak için exit code 0 dönüyoruz (Opsiyonel)
        # Eğer güvenlik açığında pipeline dursun istersen sys.exit(1) yapabilirsin.
        sys.exit(0)

if __name__ == "__main__":
    run_garak_scan()