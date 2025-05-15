pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'hello-grpc'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                sh 'docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .'
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    docker run -d --name test-container ${DOCKER_IMAGE}:${DOCKER_TAG}
                    sleep 10
                    docker ps | grep test-container
                    docker rm -f test-container
                '''
            }
        }
        
        stage('Push') {
            steps {
                script {
                    // Add your Docker registry credentials here if needed
                    // docker.withRegistry('https://your-registry', 'docker-credentials') {
                    //     docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                    // }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
} 