pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build and Test') {
            steps {
                sh 'bazel build //...'
                sh 'bazel test //...'
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
} 