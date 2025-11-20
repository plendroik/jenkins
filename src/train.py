import os
import sys
import pandas as pd
from autogluon.multimodal import MultiModalPredictor
import mlflow
from sklearn.model_selection import train_test_split
import shutil
import json
from modelscan import ModelScan  

DATA_PATH = "data/processed/final_data.csv"
MODEL_OUTPUT_DIR = "models/automm_sms_model"
STATE_PATH = "data/training_state.json"
EXPERIMENT_NAME = "AutoML_SMS_Pipeline"
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")

def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"HATA: {DATA_PATH} bulunamadi! DVC pull calisti mi?")

    print(f"Veri yukleniyor: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    

    train_data, test_data = train_test_split(df, test_size=0.2, random_state=42)
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    if os.path.exists(MODEL_OUTPUT_DIR):
        shutil.rmtree(MODEL_OUTPUT_DIR)

    with mlflow.start_run() as run:
        print("AutoGluon eğitimi başliyor...")
        mlflow.log_param("model_type", "AutoGluon-MultiModal")
        
        predictor = MultiModalPredictor(label='label', path=MODEL_OUTPUT_DIR)
        predictor.fit(train_data, time_limit=60) 
        
        scores = predictor.evaluate(test_data, metrics=["accuracy"])
        acc = scores["accuracy"]
        print(f"Accuracy: {acc:.4f}")
        mlflow.log_metric("accuracy", acc)
        
        print("-" * 50)
        print("GÜVENLİK KONTROLÜ: Model dosyaları taranıyor...")
        
        scanner = ModelScan()
        scan_results = scanner.scan(MODEL_OUTPUT_DIR)
        
        issues_count = len(scan_results.get("issues", []))
        
        if issues_count > 0:
            print(f"KRİTİK HATA: Modelde {issues_count} adet güvenlik açığı bulundu!")
            print("Detaylar:")
            print(scan_results)
            print("Model dağıtımı güvenlik nedeniyle İPTAL ediliyor.")
            sys.exit(1) 
        else:
            print("GÜVENLİK ONAYI: Tehdit bulunamadı. Model güvenli.")
            print("-" * 50)

        with open(STATE_PATH, 'w') as f:
            json.dump({"last_run_accuracy": acc, "run_id": run.info.run_id}, f)
            
        mlflow.log_artifacts(MODEL_OUTPUT_DIR, artifact_path="model")

if __name__ == "__main__":
    main()