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
                powershell 'echo "Kod cekildi."'
            }
        }

        stage('2. Ortami Kur (Setup)') {
            steps {
                powershell 'python -m venv venv'
                powershell './venv/Scripts/python -m pip install --upgrade pip'
                powershell './venv/Scripts/pip install -r requirements.txt'
            }
        }
        
        stage('3. Veri, Model ve Durumu Cek (DVC)') {
            steps {
                powershell './venv/Scripts/dvc pull data/processed/final_data.csv.dvc -f'
                
                powershell '''
                try {
                    ./venv/Scripts/dvc pull data/training_state.json.dvc -f
                } catch {
                    echo "State dosyasi henüz yok, sorun değil."
                }
                '''

                powershell '''
                $ErrorActionPreference = "Stop"
                try {
                    ./venv/Scripts/dvc pull models/automm_sms_model.dvc -f
                    echo "Onceki model cekildi."
                } catch {
                    echo "Onceki model bulunamadi (Ilk calistirma), sifirdan egitilecek."
                }
                '''
            }
        }

        stage("4. Egitim (Simulasyon)") {
            environment {
                PYTHONUTF8 = '1'
            }
            steps {
                powershell './venv/Scripts/python src/train.py'
                powershell 'echo "Egitim tamamlandi."'
            }
        }

        stage('5. S3e Yukle (DVC Push)') {
            steps {
                powershell './venv/Scripts/dvc add models/automm_sms_model'
                powershell './venv/Scripts/dvc push'
            }
        }

        stage('6. Git Push (Commit)') {
            steps {
                powershell 'git config --global user.email "jenkins@bot.com"'
                powershell 'git config --global user.name "Jenkins Bot"'
                
                powershell 'git add models/automm_sms_model.dvc'
                
                
                powershell '''
                if ( (git diff-index --quiet HEAD).ExitCode -ne 0 ) {
                    git commit -m "CI: Yeni model egitildi [skip ci]"
                    
                    # KRİTİK: Şifre sormaması için URL içine Token gömüyoruz
                    # Windows Powershell string interpolation için syntax:
                    git push https://$env:GIT_CREDS_USR:$env:GIT_CREDS_PSW@github.com/KULLANICI_ADIN/sms-automl-project.git HEAD:main
                    
                    echo "Git Push basarili."
                } else {
                    echo "Degisiklik yok."
                }
                '''
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline bitti.'
            
        }
    }
}