import os
import pandas as pd
from autogluon.multimodal import MultiModalPredictor
import mlflow
from mlflow.tracking import MlflowClient
import json

# --- Ayarlar ---
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
EXPERIMENT_NAME = "AutoML_SMS_Simulasyon"
MODEL_PATH = "automm_sms_model"            
DATA_PATH = "data/final_processed_data.csv" 
STATE_PATH = "data/training_state.json"     
BATCH_SIZE = 50                             

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r') as f:
            state = json.load(f)
            state['seen_ids'] = set(state.get('seen_ids', []))
            return state
    
    print(f"UYARI: '{STATE_PATH}' bulunamadi, sifirdan olusturuluyor.")
    return {'seen_ids': set(), 'batch_num': 0}

def save_state(seen_ids, batch_num):
    with open(STATE_PATH, 'w') as f:
        state = {'seen_ids': list(seen_ids), 'batch_num': batch_num}
        json.dump(state, f, indent=4)

def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    try: exp_id = client.create_experiment(EXPERIMENT_NAME)
    except: exp_id = client.get_experiment_by_name(EXPERIMENT_NAME).experiment_id
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"MLflow deneyi '{EXPERIMENT_NAME}' (ID: {exp_id}) ayarlandi.")

    print(f"Tüm veri havuzu '{DATA_PATH}' dosyasından yükleniyor...")
    try:
        all_data = pd.read_csv(DATA_PATH)
        all_data['message'] = all_data['message'].fillna('') 
    except FileNotFoundError:
        print(f"HATA: '{DATA_PATH}' bulunamadi. Jenkins'te 'dvc pull' adimini calistirdiniz mi?")
        exit(1)

    print(f"Önceki eğitim durumu '{STATE_PATH}' dosyasından yükleniyor...")
    state = load_state()
    seen_ids = state['seen_ids']
    batch_num = state['batch_num']
    print(f"Daha önce {len(seen_ids)} adet örnek işlenmiş.")

    label_col = 'label'
    unseen_data = all_data[~all_data['id'].isin(seen_ids)]

    if len(unseen_data) == 0:
        print("Tüm veriler zaten işlenmiş. Simülasyon başa dönüyor.")
        save_state(seen_ids=set(), batch_num=0)
        print("Durum (state) sıfırlandı. Pipeline'ı tekrar çalıştırarak baştan başlayabilirsiniz.")
        return 

    batch_to_train = unseen_data.sample(n=min(BATCH_SIZE, len(unseen_data)), random_state=42)
    print(f"Toplam {len(unseen_data)} görülmemiş örnek bulundu. {len(batch_to_train)} adetlik yeni batch işlenecek.")

    print(f"Model '{MODEL_PATH}' klasöründen yüklenecek veya sıfırdan oluşturulacak...")
    predictor = MultiModalPredictor(label=label_col, path=MODEL_PATH)

    batch_num += 1
    with mlflow.start_run(run_name=f"sim_batch_{batch_num}") as run:
        print(f"MLflow run ID: {run.info.run_id} ile batch {batch_num} eğitimi başlıyor...")
        
        mlflow.log_param("batch_num", batch_num)
        mlflow.log_param("batch_size", len(batch_to_train))
        mlflow.log_param("total_seen_samples_before_this_batch", len(seen_ids))

        predictor.fit(batch_to_train, time_limit=120) 
        print("Batch eğitimi tamamlandı.")

        y_true = batch_to_train[label_col]
        y_pred = predictor.predict(batch_to_train)
        
        from sklearn.metrics import accuracy_score
        accuracy = accuracy_score(y_true, y_pred)
        mlflow.log_metric("batch_accuracy", accuracy)
        print(f"Batch Accuracy: {accuracy:.4f}")

        new_seen_ids = seen_ids.union(set(batch_to_train['id']))
        save_state(new_seen_ids, batch_num)
        print(f"Durum güncellendi. Toplam görülen örnek: {len(new_seen_ids)}")
        
        print(f"Model '{MODEL_PATH}' klasörüne kaydedildi.")
        print("Simülasyonun bu adımı başarıyla tamamlandı.")

if __name__ == "__main__":
    main()