pipeline {
    agent any

    environment {
        MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
        
        AWS_CREDS = credentials('aws-s3-credentials')
        AWS_ACCESS_KEY_ID     = "${AWS_CREDS_USR}"
        AWS_SECRET_ACCESS_KEY = "${AWS_CREDS_PSW}"
        AWS_DEFAULT_REGION    = 'eu-north-1'
        
        GIT_CREDS = credentials('github-pat')
        
        VENV_DIR = 'venv'
    }

    stages {
        stage('1. Hazirlik (Setup)') {
            steps {
                script {
                    powershell '''
                        $env:PYTHONUTF8 = "1"
                        $env:PYTHONWARNINGS = "ignore"
                        
                        # Venv ve pip kontrolü (bozuksa onarır)
                        if ((Test-Path $env:VENV_DIR) -and (-not (Test-Path "$env:VENV_DIR\\Scripts\\pip.exe"))) {
                            Remove-Item -Recurse -Force $env:VENV_DIR
                        }
                        
                        if (-not (Test-Path $env:VENV_DIR)) {
                            python -m venv $env:VENV_DIR
                        }
                        
                        if (-not (Test-Path "$env:VENV_DIR\\Scripts\\pip.exe")) {
                             & "$env:VENV_DIR\\Scripts\\python.exe" -m ensurepip
                        }

                        # 1. Pip güncelle
                        & .\\venv\\Scripts\\python.exe -m pip install --upgrade pip
                        
                        # 2. Setuptools fix
                        & .\\venv\\Scripts\\pip.exe install "setuptools<81"
                        
                        # 3. Gereksinimleri yükle
                        & .\\venv\\Scripts\\pip.exe install -r requirements.txt
                    '''
                }
            }
        }

        stage('2. DVC Pull (Veri & Model) ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        $env:PYTHONWARNINGS = "ignore"
                        
                        echo "DVC: Veri ve Modeller çekiliyor..."
                        
                        # Veri yolu (bu değişmedi, processed içinde)
                        dvc pull data/processed/final_data.csv.dvc -f
                        
                        # DUZELTME: Model DVC dosyası artık ana dizinde
                        try { dvc pull automm_sms_model.dvc -f } catch { echo "Model yok, sıfırdan eğitim." }
                        
                        try { dvc pull data/training_state.json.dvc -f } catch { echo "State yok." }
                    '''
                }
            }
        }

        stage('3. Egitim & ModelScan') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        $env:PYTHONPATH = "$PWD"
                        $env:PYTHONWARNINGS = "ignore"
                        $env:PYTHONIOENCODING = "utf-8"
                        
                        # DUZELTME: train.py ana dizinde
                        python train.py
                    '''
                }
            }
        }

        stage('4. Garak (Red Teaming) ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        $env:PYTHONWARNINGS = "ignore"
                        $env:PYTHONIOENCODING = "utf-8"
                        
                        # Scriptler hala responsible-scripts klasöründe mi? 
                        # Eğer scriptler de ana dizindeyse yolu düzeltmelisin. 
                        # Şimdilik klasörde olduklarını varsayıyorum:
                        python responsible-scripts/run_garak.py
                    '''
                }
            }
        }

        stage('5. CycloneDX (SBOM) ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        
                        cyclonedx-py requirements requirements.txt --output-format json --output-file sbom.json
                    '''
                }
            }
        }

        stage('6. Fairlearn (Adillik) ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        $env:PYTHONWARNINGS = "ignore"
                        $env:PYTHONIOENCODING = "utf-8"
                        
                        python responsible-scripts/check_fairness.py
                    '''
                }
            }
        }

        stage('7. Giskard (Kalite) ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        $env:PYTHONWARNINGS = "ignore"
                        $env:PYTHONIOENCODING = "utf-8"
                        
                        python responsible-scripts/scan_giskard.py
                    '''
                }
            }
        }

        stage('8. Kayit & Push ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        
                        # 1. DVC'ye ekle (Model artık ana dizinde)
                        dvc add data/training_state.json automm_sms_model
                        dvc push
                        
                        # 2. Git Ayarları
                        git config --global user.email "jenkins@bot.com"
                        git config --global user.name "Jenkins Bot"
                        
                        # 3. Değişen .dvc dosyalarını ekle (yol düzeltildi)
                        git add data/training_state.json.dvc automm_sms_model.dvc
                        
                        # 4. Değişiklik varsa Commit & Push
                        $git_status = git status --porcelain
                        if ($git_status) {
                            git commit -m "CI: Pipeline basarili (ModelScan+Garak+Giskard) [skip ci]"
                            
                            # Token ile güvenli push
                            git push https://$env:GIT_CREDS_USR:$env:GIT_CREDS_PSW@github.com/plendroik/jenkins.git HEAD:main
                            echo "Git push basarili."
                        } else {
                            echo "Degisiklik yok."
                        }
                    '''
                }
            }
        }
    }
}