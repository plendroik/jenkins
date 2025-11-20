import os
import urllib.request
import pandas as pd
import zipfile
import shutil

# --- Ayarlar ---
# Verilerin duracağı yerler (Git bu klasörleri görmezden gelecek)
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"

# Klasörleri oluştur
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

def download_uci_sms():
    """UCI SMS Spam Collection verisetini indirir."""
    zip_path = os.path.join(DATA_RAW_DIR, "smsspamcollection.zip")
    
    # Eğer dosya yoksa indir
    if not os.path.exists(zip_path):
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
        print(f"İndiriliyor: {url}")
        try:
            urllib.request.urlretrieve(url, zip_path)
        except Exception as e:
            print(f"HATA: UCI verisi indirilemedi. Link ölmüş olabilir. Hata: {e}")
            return None

    # Zip'i aç
    extract_dir = os.path.join(DATA_RAW_DIR, "UCI_SMS")
    if not os.path.exists(extract_dir):
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
            
    return os.path.join(extract_dir, "SMSSpamCollection")

def download_justmarkham_sms():
    """Alternatif veri kaynağını indirir."""
    file_path = os.path.join(DATA_RAW_DIR, "sms.tsv")
    if not os.path.exists(file_path):
        url = "https://raw.githubusercontent.com/justmarkham/DAT8/master/data/sms.tsv"
        print(f"İndiriliyor: {url}")
        try:
            urllib.request.urlretrieve(url, file_path)
        except Exception as e:
            print(f"HATA: JustMarkham verisi indirilemedi. Hata: {e}")
            return None
    return file_path

def process_data():
    print("Veriler işleniyor...")
    
    # 1. UCI Verisi
    uci_path = download_uci_sms()
    if uci_path and os.path.exists(uci_path):
        df1 = pd.read_csv(uci_path, sep="\t", header=None, names=["label", "message"])
        df1['source'] = 'uci'
    else:
        df1 = pd.DataFrame() # Boş dataframe

    # 2. JustMarkham Verisi
    jm_path = download_justmarkham_sms()
    if jm_path and os.path.exists(jm_path):
        df2 = pd.read_csv(jm_path, sep="\t", header=None, names=["label", "message"])
        df2['source'] = 'justmarkham'
    else:
        df2 = pd.DataFrame()

    # Birleştirme
    if df1.empty and df2.empty:
        raise ValueError("Hiçbir veri indirilemedi! İnternet bağlantınızı kontrol edin.")

    df = pd.concat([df1, df2], ignore_index=True)
    
    # Karıştır (Shuffle)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # ID sütunu ekle (Veritabanı/Takip için önemli)
    df['id'] = df.index + 1
    
    # Eksik verileri doldur
    df['message'] = df['message'].fillna('') 

    # Basit Özellik Çıkarımı (Feature Engineering)
    df['message_len'] = df['message'].apply(len)
    df['word_count'] = df['message'].apply(lambda x: len(str(x).split()))
    
    return df

if __name__ == "__main__":
    try:
        df_final = process_data()
        
        # CSV olarak kaydet
        output_path = os.path.join(DATA_PROCESSED_DIR, "final_data.csv")
        df_final.to_csv(output_path, index=False)
        
        print("-" * 30)
        print(f"BAŞARILI: Veri '{output_path}' konumuna kaydedildi.")
        print(f"Toplam Satır Sayısı: {len(df_final)}")
        print("-" * 30)
        print("Sıradaki Adım: Bu veriyi DVC ile S3'e göndermek için şu komutları çalıştır:")
        print("1. dvc add data/processed/final_data.csv")
        print("2. dvc push")
        print("-" * 30)
        
    except Exception as e:
        print(f"KRİTİK HATA: {e}")