import os
import urllib.request
import pandas as pd
import zipfile
import re

DATA_DIR = "data" 
os.makedirs(DATA_DIR, exist_ok=True)
print(f"Veri '{DATA_DIR}' klasörüne hazırlanacak.")

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
        print("UCI SMS zip iceriği acildi.")
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

if __name__ == "__main__":
    print("Veri hazırlama script'i başlıyor...")
    final_data = load_and_merge_data()
    
    output_path = os.path.join(DATA_DIR, "final_processed_data.csv")
    final_data.to_csv(output_path, index=False)
    
    print(f"Veri hazırlandı ve '{output_path}' dosyasına kaydedildi.")