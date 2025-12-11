import pandas as pd
from autogluon.multimodal import MultiModalPredictor
import giskard
import os
import sys
from multiprocessing import freeze_support

# Sabitler
DATA_PATH = "data/processed/final_data.csv"
MODEL_PATH = "automm_sms_model"

# --- ÖNEMLİ: Modeli Global Alanda Yükleme ---
# Windows multiprocessing yapısında, prediction_function'ın bu değişkeni görebilmesi için
# modelin global alanda tanımlı olması veya class yapısı kullanılması gerekir.
# En basit çözüm, modeli burada yüklemektir.
if os.path.exists(MODEL_PATH):
    predictor = MultiModalPredictor.load(MODEL_PATH)
else:
    predictor = None  # Ana blokta kontrol edip çıkış yapacağız

def prediction_function(df):
    """
    AutoGluon modeli 'digit_count', 'has_link', 'id' gibi feature'ları eğitimde gördüğü için
    tahmin anında da bunları ister. Giskard veriyi manipüle ederken bu türetilmiş sütunları
    göndermeyebilir. Bu yüzden tahmin öncesi bunları yeniden hesaplıyoruz.
    """
    # Predictor yüklenememişse hata döndürme
    if predictor is None:
        raise ValueError("Model yüklenemediği için tahmin yapılamıyor.")

    df_proc = df.copy()
    
    # 'message' sütununun string olduğundan emin olalım (NaN hatası almamak için)
    df_proc['message'] = df_proc['message'].astype(str)

    # 1. Eksik 'id' sütunu (Model kullanıyorsa dummy indeks verelim)
    if 'id' not in df_proc.columns:
        df_proc['id'] = range(len(df_proc))
        
    # 2. Eksik 'digit_count' (Mesajdaki rakam sayısı)
    if 'digit_count' not in df_proc.columns:
        df_proc['digit_count'] = df_proc['message'].apply(lambda x: sum(c.isdigit() for c in x))
        
    # 3. Eksik 'has_link' (Link içerip içermediği)
    if 'has_link' not in df_proc.columns:
        df_proc['has_link'] = df_proc['message'].apply(lambda x: 1 if 'http' in x else 0)

    # 4. Eksik 'word_count'
    if 'word_count' not in df_proc.columns:
        df_proc['word_count'] = df_proc['message'].apply(lambda x: len(x.split()))
        
    # 5. Eksik 'message_len'
    if 'message_len' not in df_proc.columns:
        df_proc['message_len'] = df_proc['message'].apply(len)
    
    # Model tahmini
    return predictor.predict_proba(df_proc)

# --- ANA ÇALIŞTIRMA BLOĞU ---
# Bu blok, sonsuz döngü ve multiprocessing hatalarını engeller.
if __name__ == "__main__":
    # Windows için gerekli kilit (freeze) desteği
    freeze_support()

    if predictor is None:
        print(f"HATA: '{MODEL_PATH}' bulunamadı. Giskard taraması iptal ediliyor.")
        sys.exit(0)

    print("Model ve kütüphaneler yüklendi, veri hazırlanıyor...")

    # Veriyi yükle (Sadece ana işlemde yüklenmeli)
    try:
        df = pd.read_csv(DATA_PATH).head(100)
    except FileNotFoundError:
        print(f"HATA: Veri dosyası '{DATA_PATH}' bulunamadı.")
        sys.exit(1)

    # Giskard Dataset Tanımı
    giskard_dataset = giskard.Dataset(
        df=df,
        target="label",  
        name="SMS Spam Dataset"
    )

    # Giskard Model Tanımı
    giskard_model = giskard.Model(
        model=prediction_function,
        model_type="classification",
        classification_labels=predictor.class_labels,
        feature_names=["message", "source", "message_len", "word_count"], 
        name="SMS AutoGluon Model"
    )

    print("[Giskard] Güvenlik taraması (Scan) başlatılıyor. Bu işlem biraz sürebilir...")
    
    # Taramayı başlat
    scan_results = giskard.scan(giskard_model, giskard_dataset)

    # Raporu kaydet
    scan_results.to_html("giskard_report.html")
    print("[Başarılı] 'giskard_report.html' oluşturuldu.")