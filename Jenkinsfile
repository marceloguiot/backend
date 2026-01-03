pipeline {
    agent {
        docker {
            image 'docker:latest'
            // Esto es vital: "presta" el motor de Docker del servidor al contenedor
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        // Nombre de la imagen y del contenedor
        DOCKER_IMAGE = "sistpec_backend"
        DOCKER_CONTAINER = "app-sistpec_backend"
        APP_PORT = "8000"
    }

    stages {
        stage('Checkout') {
            steps {
                // Descarga el código del repositorio (GitHub/GitLab)
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                script {
                    echo '--- Construyendo Imagen Docker ---'
                    // Construye la imagen usando el Dockerfile del paso anterior
                    sh "docker build -t ${DOCKER_IMAGE}:latest ."
                }
            }
        }

        stage('Deploy / Run') {
            steps {
                script {
                    echo '--- Desplegando Contenedor ---'
                    // 1. Detener y borrar contenedor anterior si existe (para actualizar)
                    // El "|| true" evita que falle el pipeline si el contenedor no existía antes
                    sh "docker stop ${DOCKER_CONTAINER} || true"
                    sh "docker rm ${DOCKER_CONTAINER} || true"

                    // 2. Correr el nuevo contenedor
                    // -d: detached (segundo plano)
                    // -p: mapeo de puertos (Host:Contenedor)
                    // --name: nombre para identificarlo
                    sh """
                        docker run -d \
                        -p ${APP_PORT}:8000 \
                        --name ${DOCKER_CONTAINER} \
                        --restart always \
                        ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }
    }
    
    post {
        always {
            // Limpieza opcional de imágenes "dangling" (sin etiqueta) para ahorrar espacio
            sh "docker image prune -f"
        }
        success {
            echo '¡Despliegue Exitoso!'
        }
        failure {
            echo 'El despliegue falló.'
        }
    }
}