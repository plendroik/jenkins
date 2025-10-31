pipeline {
    agent any 

    stages {
        stage('1. Kodu Cek (Checkout)') {
            steps {
                checkout scm
            }
        }
        stage('2. Ortami Kur (Setup)') {
            steps {

                powershell 'python -m pip install --upgrade pip'
                powershell 'python -m pip install -r requirements.txt'
            }
        }
        stage('3. Modeli Egit ve MLflowa Kaydet (Train)') {
            environment {
                // Python'a tüm I/O işlemleri için UTF-8 kullanmasını söyler
                PYTHONUTF8 = '1'
            }
            steps {
                powershell 'python train.py'
            }
        }
    }
    post {
        always {
            echo 'Windows Pipeline (PowerShell ile) bitti.'
        }
    }
}