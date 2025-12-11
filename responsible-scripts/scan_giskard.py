import pandas as pd
from autogluon.multimodal import MultiModalPredictor
import giskard
import os
import sys

DATA_PATH = "data/processed/final_data.csv"
MODEL_PATH = "automm_sms_model"

if not os.path.exists(MODEL_PATH):
    print("Model yok, Giskard taraması atlanıyor.")
    sys.exit(0)

# Veriyi yükle
df = pd.read_csv(DATA_PATH).head(100) 

# Modeli yükle
predictor = MultiModalPredictor.load(MODEL_PATH)

# Giskard Dataset Tanımı
# Not: Burada raw veri setini veriyoruz.
giskard_dataset = giskard.Dataset(
    df=df,
    target="label",  
    name="SMS Spam Dataset"
)

# --- DÜZELTME BURADA ---
def prediction_function(df):
    """
    AutoGluon modeli 'digit_count', 'has_link', 'id' gibi feature'ları eğitimde gördüğü için
    tahmin anında da bunları ister. Giskard veriyi manipüle ederken bu türetilmiş sütunları
    göndermeyebilir. Bu yüzden tahmin öncesi bunları yeniden hesaplıyoruz.
    """
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

# Giskard Model Tanımı
giskard_model = giskard.Model(
    model=prediction_function,
    model_type="classification",
    classification_labels=predictor.class_labels,
    # feature_names: Giskard'ın manipüle edeceği temel sütunları belirtir.
    # Türetilmiş sütunları (digit_count vb.) buraya yazmak yerine yukarıda hesaplattık.
    feature_names=["message", "source", "message_len", "word_count"], 
    name="SMS AutoGluon Model"
)

print("[Giskard] Güvenlik taraması (Scan) başlatılıyor. Bu işlem biraz sürebilir...")
scan_results = giskard.scan(giskard_model, giskard_dataset)

scan_results.to_html("giskard_report.html")
print("[Başarılı] 'giskard_report.html' oluşturuldu.")