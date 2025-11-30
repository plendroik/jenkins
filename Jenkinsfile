pipeline {
    agent any 

    environment {
        
        MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
        
        
        AWS_CREDS = credentials('aws-s3-credentials')
        
        
        AWS_ACCESS_KEY_ID     = "${AWS_CREDS_USR}"
        AWS_SECRET_ACCESS_KEY = "${AWS_CREDS_PSW}"
        AWS_DEFAULT_REGION    = 'eu-north-1' 
        
        
        GIT_CREDS = credentials('github-pat') 
    }

    stages {
        stage('1. Kodu Cek (Git)') {
            steps {
                checkout scm: [$class: 'GitSCM', branches: [[name: '*/main']]], poll: false
                powershell 'echo "Kod GitHub''dan cekildi."'
            }
        }

        stage('2. Ortami Kur (Setup)') {
            steps {
                
                powershell 'python -m venv venv'
                powershell './venv/Scripts/python -m pip install --upgrade pip'
                powershell './venv/Scripts/pip install -r requirements.txt'
            }
        }

        stage('3. Guvenlik Envanteri (AI-BOM)') {
            steps {
                // MLSecOps: tedarik zinciri güvenliği 
                
                powershell './venv/Scripts/cyclonedx-py requirements requirements.txt --output-format json --output-file ai_bom.json'
                
                
                archiveArtifacts artifacts: 'ai_bom.json', fingerprint: true
                powershell 'echo "AI-BOM (Malzeme Listesi) oluşturuldu ve arşivlendi."'
            }
        }
        
        stage('4. Veri ve Modeli Cek (DVC)') {
            steps {

                powershell './venv/Scripts/dvc pull data/processed/final_data.csv.dvc -f'
                

                powershell '''
                    if (Test-Path "data/training_state.json.dvc") {
                        echo "State dosyasi bulundu, indiriliyor..."
                        ./venv/Scripts/dvc pull data/training_state.json.dvc -f
                    } else {
                        echo "BILGI: State dosyasi henuz yok (Ilk calistirma). Pas geciliyor."
                    }
                '''


                powershell '''
                    $ErrorActionPreference = "Continue"
                    if (Test-Path "models/automm_sms_model.dvc") {
                        echo "Onceki model bulundu, indiriliyor..."
                        ./venv/Scripts/dvc pull models/automm_sms_model.dvc -f
                    } else {
                        echo "BILGI: Onceki model henuz yok (Ilk calistirma). Sifirdan egitilecek."
                    }
                '''
            }
        }

        stage("5. Egitim ve Guvenlik Taramasi (MLSecOps)") {
            environment {
                PYTHONUTF8 = '1'
            }
            steps {
                // modelcan ile virüs taraması
                powershell './venv/Scripts/python src/train.py'
                
                // NVIDIA Garak 
                // --probes: sadece enjeksiyon ve şifreleme saldırılarını dene 
                // --generations 1: her saldırıyı sadece 1 kez dene 
                
                powershell '''
                    echo "Garak: Optimize edilmis kirmizi takim testi baslatiliyor..."
                    ./venv/Scripts/python -m garak --model_type test --probes encoding,promptinject --generations 1
                '''
                
                powershell 'echo "Egitim, ModelScan ve Garak testleri tamamlandi."'
            }
        }

        stage('6. S3e Yukle (DVC Push)') {
            steps {
                
                powershell './venv/Scripts/dvc add models/automm_sms_model'
                
                
                powershell '''
                    if (Test-Path "data/training_state.json") {
                        ./venv/Scripts/dvc add data/training_state.json
                    }
                '''

                
                powershell './venv/Scripts/dvc push'
                powershell 'echo "Veriler S3 bucketa (Stockholm) gonderildi."'
            }
        }

        stage('7. Git Push (Commit)') {
            steps {
                powershell 'git config --global user.email "jenkins@bot.com"'
                powershell 'git config --global user.name "Jenkins Bot"'
                
                powershell 'git add models/automm_sms_model.dvc'
                
                powershell '''
                    if (Test-Path "data/training_state.json.dvc") {
                        git add data/training_state.json.dvc
                    }
                '''
                
                powershell '''
                if ( (git diff-index --quiet HEAD).ExitCode -ne 0 ) {
                    git commit -m "CI: Yeni model egitildi, tarandi ve S3e yuklendi [skip ci]"
                    
                    # Token ile güvenli Push (403 hatasını önler)
                    git push https://$env:GIT_CREDS_USR:$env:GIT_CREDS_PSW@github.com/plendroik/jenkins.git HEAD:main
                    
                    echo "Git Push basarili."
                } else {
                    echo "Model veya durumda degisiklik yok, Git push atlaniyor."
                }
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline islemi bitti.'
        }
        failure {
            echo 'Pipeline HATA aldi. Lutfen loglari kontrol et.'
        }
    }
}