pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Setup') {
            steps {
                sh 'python -m venv venv'
                sh '. venv/bin/activate'
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Run Ingestion') {
            steps {
                sh '. venv/bin/activate && python src/data/ingestion.py'
            }
        }
        stage('Run Pipeline') {
            steps {
                sh '. venv/bin/activate && python main.py'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'logs/**/*.log', allowEmptyArchive: true
        }
    }
}