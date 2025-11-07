import os
import pandas as pd
from autogluon.multimodal import MultiModalPredictor
import mlflow
from mlflow.tracking import MlflowClient
import json
import shutil 

# --- Ayarlar ---
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
EXPERIMENT_NAME = "AutoML_SMS_Simulasyon"
MODEL_PATH = "automm_sms_model"            
DATA_PATH = "data/final_processed_data.csv" 
STATE_PATH = "data/training_state.json"     
BATCH_SIZE = 2000

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            state = json.load(f)
            state['seen_ids'] = set(state.get('seen_ids', []))
            return state
    
    print(f"UYARI: '{STATE_PATH}' bulunamadi, sifirdan olusturuluyor.")
    return {'seen_ids': set(), 'batch_num': 0}

def save_state(seen_ids, batch_num):
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        state = {'seen_ids': list(seen_ids), 'batch_num': batch_num}
        json.dump(state, f, indent=4)

def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    try: exp_id = client.create_experiment(EXPERIMENT_NAME)
    except: exp_id = client.get_experiment_by_name(EXPERIMENT_NAME).experiment_id
    print(f"MLflow deneyi '{EXPERIMENT_NAME}' (ID: {exp_id}) ayarlandi.")

    print(f"Tum veri havuzu '{DATA_PATH}' dosyasindan yukleniyor...")
    try:
        all_data = pd.read_csv(DATA_PATH)
        all_data['message'] = all_data['message'].fillna('') 
    except FileNotFoundError:
        print(f"HATA: '{DATA_PATH}' bulunamadi. Jenkins'te 'dvc pull' adimini calistirdiniz mi?")
        exit(1)

    print(f"Onceki egitim durumu '{STATE_PATH}' dosyasindan yukleniyor...")
    state = load_state()
    seen_ids = state['seen_ids']
    batch_num = state['batch_num']
    print(f"Daha once {len(seen_ids)} adet ornek islenmis.")

    label_col = 'label'
    unseen_data = all_data[~all_data['id'].isin(seen_ids)]

    if len(unseen_data) == 0:
        print("Tum veriler zaten islenmis. Simulasyon basa donuyor.")
        save_state(seen_ids=set(), batch_num=0)
        print("Durum (state) sifirlandi. Pipeline'i tekrar calistirarak bastan baslayabilirsiniz.")
        return 

    batch_to_train = unseen_data.sample(n=min(BATCH_SIZE, len(unseen_data)), random_state=42)
    print(f"Toplam {len(unseen_data)} gorulmemis ornek bulundu. {len(batch_to_train)} adetlik yeni batch islenecek.")

    try:
        predictor = MultiModalPredictor.load(MODEL_PATH)
        print(f"Mevcut model '{MODEL_PATH}' klasorunden yuklendi. Fine-tuning basliyor...")
    except:
        print(f"Mevcut model '{MODEL_PATH}' yuklenemedi veya gecersiz. Sifirdan egitim basliyor...")
        
        if os.path.exists(MODEL_PATH):
            shutil.rmtree(MODEL_PATH)
            
        predictor = MultiModalPredictor(label=label_col, path=MODEL_PATH)
    

    batch_num += 1
    with mlflow.start_run(run_name=f"sim_batch_{batch_num}") as run:
        print(f"MLflow run ID: {run.info.run_id} ile batch {batch_num} egitimi basliyor...")
        
        mlflow.log_param("batch_num", batch_num)
        mlflow.log_param("batch_size", len(batch_to_train))
        mlflow.log_param("total_seen_samples_before_this_batch", len(seen_ids))

        predictor.fit(batch_to_train, time_limit=120) 
        print("Batch egitimi tamamlandi.")

        y_true = batch_to_train[label_col]
        y_pred = predictor.predict(batch_to_train)
        
        from sklearn.metrics import accuracy_score
        accuracy = accuracy_score(y_true, y_pred)
        mlflow.log_metric("batch_accuracy", accuracy)
        print(f"Batch Accuracy: {accuracy:.4f}")

        new_seen_ids = seen_ids.union(set(batch_to_train['id']))
        save_state(new_seen_ids, batch_num)
        print(f"Durum guncellendi. Toplam gorulen ornek: {len(new_seen_ids)}")
        
        print(f"Model '{MODEL_PATH}' klasorune kaydedildi.")
        print("Simulasyonun bu adimi basariyla tamamlandi.")

if __name__ == "__main__":
    main()