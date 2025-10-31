import os
import urllib.request
import pandas as pd
import zipfile
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT_NAME = "Simple_SMS_Model"
DATA_DIR = "datasets"

os.makedirs(DATA_DIR, exist_ok=True)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
try:
    exp_id = client.create_experiment(EXPERIMENT_NAME)
except Exception:
    exp_id = client.get_experiment_by_name(EXPERIMENT_NAME).experiment_id
mlflow.set_experiment(EXPERIMENT_NAME)
print(f"MLflow deneyi '{EXPERIMENT_NAME}' (ID: {exp_id}) ayarlandi.")

def download_uci_sms():
    zip_path = os.path.join(DATA_DIR, "smsspamcollection.zip")
    if not os.path.exists(zip_path):
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
        print("UCI SMS Spam Collection indiriliyor...")
        urllib.request.urlretrieve(url, zip_path)
        print("UCI SMS indirildi.")
    
    extract_dir = os.path.join(DATA_DIR, "UCI_SMS")
    if not os.path.exists(extract_dir):
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
        print("UCI SMS zip icerigi acildi.")
    return os.path.join(extract_dir, "SMSSpamCollection")

def download_justmarkham_sms():
    file_path = os.path.join(DATA_DIR, "sms.tsv")
    if not os.path.exists(file_path):
        url = "https://raw.githubusercontent.com/justmarkham/DAT8/master/data/sms.tsv"
        print("JustMarkham sms.tsv indiriliyor...")
        urllib.request.urlretrieve(url, file_path)
        print("JustMarkham sms.tsv indirildi.")
    return file_path

def load_and_merge_data():
    uci_file = download_uci_sms()
    df1 = pd.read_csv(uci_file, sep="\t", header=None, names=["label", "message"])
    df1['source'] = 'uci'

    jm_file = download_justmarkham_sms()
    df2 = pd.read_csv(jm_file, sep="\t", header=None, names=["label", "message"])
    df2['source'] = 'justmarkham'

    df = pd.concat([df1, df2], ignore_index=True)

    df = df.sample(frac=1, random_state=1).reset_index(drop=True)
    df['id'] = df.index + 1
    
    df['message_len'] = df['message'].apply(len)
    df['word_count'] = df['message'].apply(lambda x: len(str(x).split()))
    df['has_link'] = df['message'].str.contains('http|www|https', regex=True).astype(int)
    df['digit_count'] = df['message'].str.count(r'\d').fillna(0).astype(int)
    
    df['message'] = df['message'].fillna('') 
    return df


def main():
    print("Veri yükleme ve birleştirme işlemi başlıyor...")
    data = load_and_merge_data()
    print("Veri yüklendi. Özellikler oluşturuldu.")

    label_col = 'label'
    text_feature = 'message'
    numeric_features = ['message_len', 'word_count', 'has_link', 'digit_count']

    X = data[numeric_features + [text_feature]]
    y = data[label_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preprocessor = ColumnTransformer(
        transformers=[
            ('text', TfidfVectorizer(), text_feature),
            ('numeric', StandardScaler(), numeric_features)
        ],
        remainder='drop' # 
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(random_state=42, max_iter=1000))
    ])

    print("MLflow deneyi başlıyor...")
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"Run ID: {run_id}")
        
        mlflow.log_param("model_type", "LogisticRegression")
        mlflow.log_param("text_vectorizer", "TfidfVectorizer")
        mlflow.log_param("numeric_scaler", "StandardScaler")
        mlflow.log_param("train_test_split_ratio", 0.2)
        mlflow.log_param("dataset_size", len(data))

        print("Model eğitimi başlıyor...")
        pipeline.fit(X_train, y_train)
        print("Model eğitimi tamamlandı.")

        y_pred = pipeline.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')

        mlflow.log_metric("test_accuracy", accuracy)
        mlflow.log_metric("test_f1_score", f1)
        
        print(f"Test Sonuçları: Accuracy = {accuracy:.4f}, F1 Score = {f1:.4f}")

        mlflow.sklearn.log_model(pipeline, "model")
        print("Model, MLflow'a 'model' adıyla kaydedildi.")

if __name__ == "__main__":
    main()