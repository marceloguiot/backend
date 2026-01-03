pipeline {
    agent any

    environment {
        // Carpeta para aislar las librerías
        VENV_NAME = "venv"
        // Puerto definido por uvicorn standard
        APP_PORT = "8000"
        // Evita que Jenkins mate el proceso al terminar
        JENKINS_NODE_COOKIE = "dontKillMe" 
    }

    stages {
        stage('Limpiar Entorno') {
            steps {
                // Elimina entorno virtual anterior para asegurar una instalación limpia
                sh "rm -rf ${VENV_NAME} || true"
            }
        }

        stage('Instalar Dependencias') {
            steps {
                script {
                    echo '--- Creando Virtual Environment ---'
                    // Crea el entorno virtual con Python 3
                    sh "python3 -m venv ${VENV_NAME}"
                    
                    echo '--- Instalando Librerías ---'
                    // Instala lo que tienes en requirements.txt (FastAPI, SQLAlchemy, etc.)
                    sh """
                        . ${VENV_NAME}/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    """
                }
            }
        }

        stage('Desplegar API') {
            steps {
                script {
                    echo '--- Levantando FastAPI ---'
                    
                    // 1. Matar proceso anterior si existe (para liberar el puerto 8000)
                    // Si falla fuser, intenta con pkill
                    sh "fuser -k ${APP_PORT}/tcp || true"
                    
                    // Pausa de seguridad
                    sleep 2

                    // 2. Ejecutar Uvicorn en segundo plano (nohup)
                    // Usamos uvicorn main:app como indica tu standard
                    sh """
                        . ${VENV_NAME}/bin/activate
                        nohup uvicorn main:app --host 0.0.0.0 --port ${APP_PORT} > salida.log 2>&1 &
                    """
                }
            }
        }
    }

    post {
        success {
            echo "¡Éxito! Tu API está corriendo (probablemente en http://IP-DEL-SERVIDOR:8000)"
        }
        failure {
            echo "Falló el despliegue. Revisa los logs."
        }
    }
}