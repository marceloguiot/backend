pipeline {
    agent any

    environment {
        APP_PORT = "8000"
        JENKINS_NODE_COOKIE = "dontKillMe"
        // Añadimos la ruta local al PATH para asegurar que encuentre las herramientas instaladas
        PATH = "${HOME}/.local/bin:${PATH}"
    }

    stages {
        stage('Preparar PIP (Bootstrap)') {
            steps {
                script {
                    echo '--- Descargando e instalando PIP manualmente ---'
                    // 1. Descarga el instalador oficial de PIP (get-pip.py)
                    // Usamos curl. Si falla, intenta con wget.
                    sh """
                        curl -sS https://bootstrap.pypa.io/get-pip.py -o get-pip.py || wget https://bootstrap.pypa.io/get-pip.py
                    """

                    // 2. Ejecuta el instalador solo para el usuario actual
                    // --break-system-packages es necesario en Python 3.11+ cuando no usas venv
                    sh "python3 get-pip.py --user --break-system-packages"
                    
                    // 3. Verifica que se instaló
                    sh "python3 -m pip --version"
                }
            }
        }

        stage('Instalar Dependencias') {
            steps {
                script {
                    echo '--- Instalando requirements.txt ---'
                    // Usamos "python3 -m pip" que es más seguro que llamar a "pip" directamente
                    sh "python3 -m pip install --user -r requirements.txt --break-system-packages"
                }
            }
        }

        stage('Desplegar API') {
            steps {
                script {
                    echo '--- Levantando FastAPI ---'
                    
                    // 1. Matar proceso anterior
                    sh "fuser -k ${APP_PORT}/tcp || true"
                    sleep 2

                    // 2. Ejecutar Uvicorn
                    sh """
                        nohup python3 -m uvicorn main:app --host 0.0.0.0 --port ${APP_PORT} > salida.log 2>&1 &
                    """
                }
            }
        }
    }

    post {
        success {
            echo "¡Despliegue exitoso! API corriendo en puerto ${APP_PORT}"
        }
        failure {
            echo "Falló el despliegue. Revisa los logs."
        }
    }
}