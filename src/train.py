import os
import pandas as pd
from autogluon.multimodal import MultiModalPredictor
import mlflow
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
import shutil
import warnings
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings('ignore')

DATA_PATH = "data/processed/final_data.csv"
MODEL_OUTPUT_DIR = "models/automm_sms_model" 
EXPERIMENT_NAME = "AutoML_SMS_Pipeline"

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
ARTIFACT_URI = f"s3://{S3_BUCKET_NAME}/mlflow-artifacts" if S3_BUCKET_NAME else "./mlruns"

def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"HATA: {DATA_PATH} bulunamadı! 'dvc pull' yapıldı mı?")

    df = pd.read_csv(DATA_PATH)
    
    
    train_data, test_data = train_test_split(df, test_size=0.2, random_state=42)
    
    mlflow.set_tracking_uri("./mlruns") 
    client = MlflowClient()
    
    try:
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        exp_id = experiment.experiment_id
    except:
        print(f"Yeni deney oluşturuluyor. Hedef: {ARTIFACT_URI}")
        exp_id = client.create_experiment(EXPERIMENT_NAME, artifact_location=ARTIFACT_URI)
    
    mlflow.set_experiment(experiment_id=exp_id)

    if os.path.exists(MODEL_OUTPUT_DIR):
        shutil.rmtree(MODEL_OUTPUT_DIR)

    print(f"Eğitim başlıyor... Model Artifactleri şuraya gidecek: {ARTIFACT_URI}")
    
    with mlflow.start_run() as run:
        mlflow.log_param("model_framework", "AutoGluon")
        mlflow.log_param("data_source", "S3 via DVC")

        predictor = MultiModalPredictor(label='label', path=MODEL_OUTPUT_DIR)
        predictor.fit(train_data, time_limit=120) 
        
        y_pred = predictor.predict(test_data)
        acc = accuracy_score(test_data['label'], y_pred)
        mlflow.log_metric("accuracy", acc)
        print(f"Accuracy: {acc:.4f}")

        print("Model S3'e yükleniyor...")
        mlflow.log_artifacts(MODEL_OUTPUT_DIR, artifact_path="model")
        
        print(f"Başarılı! Model S3 bucket: {S3_BUCKET_NAME} içinde saklandı.")

if __name__ == "__main__":
    main()