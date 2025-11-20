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
                powershell 'echo "Kod GitHubdan cekildi."'
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
                    if (Test-Path "data/training_state.json.dvc") {
                        echo "State dosyasi indiriliyor..."
                        ./venv/Scripts/dvc pull data/training_state.json.dvc -f
                    } else {
                        echo "BILGI: State dosyasi henuz yok (Ilk calistirma)."
                    }
                '''

                
                powershell '''
                    $ErrorActionPreference = "Continue"
                    if (Test-Path "models/automm_sms_model.dvc") {
                        echo "Eski model indiriliyor..."
                        ./venv/Scripts/dvc pull models/automm_sms_model.dvc -f
                    } else {
                        echo "BILGI: Eski model henuz yok (Ilk calistirma)."
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
                
                
                powershell '''
                    if (Test-Path "data/training_state.json") {
                        ./venv/Scripts/dvc add data/training_state.json
                    }
                '''

                
                powershell './venv/Scripts/dvc push'
            }
        }

        stage('6. Git Push (Commit)') {
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
                    git commit -m "CI: Yeni model egitildi [skip ci]"
                    
                    # Token ile güvenli push
                    git push https://$env:GIT_CREDS_USR:$env:GIT_CREDS_PSW@github.com/plendroik/jenkins.git HEAD:main
                    
                    echo "Git Push basarili."
                } else {
                    echo "Degisiklik yok, Git push atlaniyor."
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