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


df = pd.read_csv(DATA_PATH).head(100) 

predictor = MultiModalPredictor.load(MODEL_PATH)

giskard_dataset = giskard.Dataset(
    df=df,
    target="label",  
    
    name="SMS Spam Dataset"
)


def prediction_function(df):
    return predictor.predict_proba(df)

giskard_model = giskard.Model(
    model=prediction_function,
    model_type="classification",
    classification_labels=predictor.class_labels,
    feature_names=["message", "source", "message_len", "word_count"], 
    name="SMS AutoGluon Model"
)

print("[Giskard] Güvenlik taraması (Scan) başlatılıyor. Bu işlem biraz sürebilir...")
scan_results = giskard.scan(giskard_model, giskard_dataset)

scan_results.to_html("giskard_report.html")
print("[Başarılı] 'giskard_report.html' oluşturuldu.")