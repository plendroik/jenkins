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

        stage('3. Guvenlik Envanteri (AI-BOM)') {
            steps {
                powershell './venv/Scripts/cyclonedx-py environment --outfile ai_bom.json'
                archiveArtifacts artifacts: 'ai_bom.json', fingerprint: true
                powershell 'echo "AI-BOM oluşturuldu."'
            }
        }
        
        stage('4. Veri ve Modeli Cek (DVC)') {
            steps {
                powershell './venv/Scripts/dvc pull data/processed/final_data.csv.dvc -f'
                
                powershell '''
                    if (Test-Path "data/training_state.json.dvc") {
                        ./venv/Scripts/dvc pull data/training_state.json.dvc -f
                    }
                    if (Test-Path "models/automm_sms_model.dvc") {
                        ./venv/Scripts/dvc pull models/automm_sms_model.dvc -f
                    }
                '''
            }
        }

        stage("5. Egitim ve Guvenlik Taramasi") {
            environment {
                PYTHONUTF8 = '1'
            }
            steps {
                powershell './venv/Scripts/python src/train.py'
                powershell 'echo "Egitim ve Guvenlik taramasi tamamlandi."'
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
                    git commit -m "CI: Yeni model egitildi ve tarandi [skip ci]"
                    git push https://$env:GIT_CREDS_USR:$env:GIT_CREDS_PSW@github.com/plendroik/jenkins.git HEAD:main
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
        failure {
            echo 'HATA: Guvenlik taramasi veya egitim basarisiz oldu.'
        }
    }
}