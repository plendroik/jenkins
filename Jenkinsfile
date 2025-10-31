pipeline {
    agent any 

    stages {
        stage('1. Kodu Çek (Checkout)') {
            steps {
                checkout scm
            }
        }
        stage('2. Ortamı Kur (Setup)') {
            steps {
                bat 'python -m pip install --upgrade pip'
                bat 'python -m pip install -r requirements.txt'
            }
        }
        stage('3. Modeli Eğit ve MLflowa Kaydet (Train)') {
            steps {
                bat 'python main.py'
            }
        }
    }
    post {
        always {
            echo 'Windows Pipeline bitti.'
        }
    }
}