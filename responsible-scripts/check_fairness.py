import pandas as pd
from autogluon.multimodal import MultiModalPredictor
from fairlearn.metrics import MetricFrame, accuracy_score, selection_rate
import os
import sys

DATA_PATH = "data/final_processed_data.csv"
MODEL_PATH = "automm_sms_model"

print(f"[Fairlearn] Veri ({DATA_PATH}) ve Model ({MODEL_PATH}) kontrol ediliyor...")

if not os.path.exists(MODEL_PATH):
    print("UYARI: Model klasörü bulunamadı. Eğitim adımı başarısız olmuş veya ilk çalıştırış olabilir.")
    sys.exit(0) 

try:
    df = pd.read_csv(DATA_PATH)

    df_sample = df.sample(n=min(500, len(df)), random_state=42)
except Exception as e:
    print(f"HATA: Veri okunamadı. {e}")
    sys.exit(1)


try:
    predictor = MultiModalPredictor.load(MODEL_PATH)
except Exception as e:
    print(f"HATA: Model yüklenemedi. {e}")
    sys.exit(1)


y_true = df_sample['label']
y_pred = predictor.predict(df_sample)

if 'source' in df_sample.columns:
    sensitive_feature = df_sample['source']
    print("[Fairlearn] 'source' gruplarına göre analiz yapılıyor...")
    
    mf = MetricFrame(
        metrics={'accuracy': accuracy_score, 'selection_rate': selection_rate},
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_feature
    )
    
    print("\n--- FAIRNESS RAPORU ---")
    print(mf.by_group)
    

    mf.by_group.to_json("fairness_report.json")
    print("\n[Başarılı] Rapor 'fairness_report.json' olarak kaydedildi.")
else:
    print("UYARI: 'source' sütunu bulunamadı, analiz yapılamadı.")