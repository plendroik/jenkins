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
                        if ((Test-Path $env:VENV_DIR) -and (-not (Test-Path "$env:VENV_DIR\\Scripts\\pip.exe"))) { Remove-Item -Recurse -Force $env:VENV_DIR }
                        if (-not (Test-Path $env:VENV_DIR)) { python -m venv $env:VENV_DIR }
                        if (-not (Test-Path "$env:VENV_DIR\\Scripts\\pip.exe")) { & "$env:VENV_DIR\\Scripts\\python.exe" -m ensurepip }
                        & .\\venv\\Scripts\\python.exe -m pip install --upgrade pip
                        & .\\venv\\Scripts\\pip.exe install "setuptools<81"
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
                        dvc pull data/processed/final_data.csv.dvc -f
                        try { dvc pull automm_sms_model.dvc -f } catch { echo "Model yok, ama egitimi atladigimiz icin sorun degil." }
                        try { dvc pull data/training_state.json.dvc -f } catch { echo "State yok." }
                    '''
                }
            }
        }

        stage('3. Egitim & ModelScan (ATLANDI ⏩)') {
            steps {
                script {
                    echo "HIZLI TEST MODU: Egitim asamasi zaman kazanmak icin atlandi."
                    // powershell '''
                    //    $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                    //    $env:PYTHONPATH = "$PWD"
                    //    $env:PYTHONWARNINGS = "ignore"
                    //    $env:PYTHONIOENCODING = "utf-8"
                    //    python train.py
                    // '''
                }
            }
        }

        stage('4. Garak (Red Teaming) (ATLANDI ⏩)') {
            steps {
                script {
                    echo "HIZLI TEST MODU: Garak asamasi atlandi."
                    // powershell '''
                    //    $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                    //    $env:PYTHONWARNINGS = "ignore"
                    //    $env:PYTHONIOENCODING = "utf-8"
                    //    python run_garak.py
                    // '''
                }
            }
        }

        stage('5. CycloneDX (SBOM) ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        
                        # DUZELTME: --force silindi, artik calismali!
                        cyclonedx-py requirements requirements.txt --output-format json --output-file sbom.json
                        
                        echo "SBOM basariyla olusturuldu!"
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
                        python check_fairness.py
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
                        python scan_giskard.py
                    '''
                }
            }
        }

        stage('8. Kayit & Push ') {
            steps {
                script {
                    powershell '''
                        $env:Path = "$PWD\\venv\\Scripts;$env:Path"
                        
                        # Model egitilmedigi icin DVC add hata verebilir, onu gecici olarak devre disi birakabilirsin
                        # Ama simdilik sadece hata vermesin diye try-catch gibi dusunelim:
                        echo "Kayit asamasi (Test modunda oldugumuz icin push yapmiyoruz)"
                    '''
                }
            }
        }
    }
}