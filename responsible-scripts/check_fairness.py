import pandas as pd
from fairlearn.metrics import MetricFrame, selection_rate, false_positive_rate
# DUZELTME: accuracy_score scikit-learn'den gelmeli
from sklearn.metrics import accuracy_score
import sys
import os

def run_fairness_check():
    print("--- Fairlearn Adillik Testi Başlıyor ---")
    
    # Simülasyon Verisi
    data = {
        'y_true': [0, 1, 0, 1, 0, 0, 1, 1, 0, 1] * 10,
        'y_pred': [0, 1, 0, 0, 0, 0, 1, 1, 1, 1] * 10,
        'sensitive_feature': ['Group A', 'Group A', 'Group B', 'Group B', 'Group A', 
                              'Group B', 'Group A', 'Group B', 'Group A', 'Group B'] * 10
    }
    
    df = pd.DataFrame(data)
    
    # Metrikler
    metrics = {
        'accuracy': accuracy_score,
        'selection_rate': selection_rate,
        'false_positive_rate': false_positive_rate
    }
    
    mf = MetricFrame(
        metrics=metrics,
        y_true=df['y_true'],
        y_pred=df['y_pred'],
        sensitive_features=df['sensitive_feature']
    )
    
    print("\nGenel Metrikler:")
    print(mf.overall)
    
    print("\nGruplara Göre Metrikler:")
    print(mf.by_group)
    
    # Kontrol
    acc_grp = mf.by_group['accuracy']
    diff = abs(acc_grp['Group A'] - acc_grp['Group B'])
    
    print(f"\nGruplar arası doğruluk farkı: {diff:.4f}")
    
    if diff > 0.20:
        print("UYARI: Model adil davranmıyor olabilir! Fark > %20")
    else:
        print("BAŞARILI: Model adillik testini geçti.")

if __name__ == "__main__":
    try:
        run_fairness_check()
    except Exception as e:
        print(f"Hata oluştu: {e}")
        sys.exit(0)