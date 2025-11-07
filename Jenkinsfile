pipeline {
    agent any 

    environment {
        MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
        
        // Jenkins Credentials ID'leri (GUVENLI YONTEM)
        AWS_ACCESS_KEY_ID     = credentials('jenkins-aws-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('jenkins-aws-secret-key')
        AWS_DEFAULT_REGION    = 'eu-north-1'
    }

    stages {
        stage('1. Kodu Cek (Git)') {
            steps {
                checkout scm
                powershell 'echo "Kod cekildi."'
            }
        }
        stage('2. Ortami Kur (Setup)') {
            steps {
                powershell 'python -m pip install --upgrade pip'
                powershell 'python -m pip install -r requirements.txt'
            }
        }
        
        // *** DUZELTME BURADA BASLIYOR ***
        stage('3. Veri, Model ve Durumu Cek (DVC)') {
            steps {
                // 1. Ana veriyi cek (Bu basarili olmali)
                powershell 'dvc pull data/final_processed_data.csv.dvc -f'
                
                // 2. Durum dosyasini cek (try...catch ile)
                powershell '''
                try {
                    dvc pull data/training_state.json.dvc -f
                    echo "Onceki 'training_state.json' cekildi."
                } catch {
                    echo "Onceki 'training_state.json' bulunamadi (Ilk calistirma, bu normaldir)."
                }
                '''
                
                // 3. Model dosyasini cek (try...catch ile)
                powershell '''
                try {
                    dvc pull automm_sms_model.dvc -f
                    echo "Onceki 'automm_sms_model' cekildi."
                } catch {
                    echo "Onceki 'automm_sms_model' bulunamadi (Ilk calistirma, bu normaldir)."
                }
                '''
                
                powershell 'echo "DVC pull adimi tamamlandi."'
            }
        }
        // *** DUZELTME BURADA BITIYOR ***

        stage("4. Bir Sonraki Batch'i Egit (Simulasyon)") {
            environment {
                PYTHONUTF8 = '1'
            }
            steps {
                powershell 'python train.py'
                powershell 'echo "Egitim tamamlandi."'
            }
        }
        stage('5. Yeni Model ve Durumu Kaydet (DVC Push)') {
            steps {
                powershell 'dvc add data/training_state.json automm_sms_model'
                powershell 'dvc push'
                powershell 'echo "Yeni model ve durum S3''e gonderildi."'
            }
        }
        stage('6. Isaretcileri Kaydet (Git Push)') {
            steps {
                powershell 'git config --global user.email "jenkins-ci@example.com"'
                powershell 'git config --global user.name "Jenkins CI"'
                powershell 'git add data/training_state.json.dvc automm_sms_model.dvc'
                powershell '''
                if ( (git diff-index --quiet HEAD).ExitCode -ne 0 ) {
                    git commit -m "CI: Simulasyonun yeni adimi (model ve durum) eklendi [skip ci]"
                    git push
                    echo "Yeni model ve durum isaretcileri Git''e gonderildi."
                } else {
                    echo "Model veya durumda degisiklik yok, Git push atlaniyor."
                }
                '''
            }
        }
    }
    post {
        always {
            echo 'MLOps Simulasyon Pipeline Adimi tamamlandi.'
        }
    }
}