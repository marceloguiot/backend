pipeline {
    agent any

    environment {
        APP_PORT = "8000"
        JENKINS_NODE_COOKIE = "dontKillMe"
        // Agregamos la ruta local de binarios al PATH para que encuentre 'uvicorn'
        PATH = "${HOME}/.local/bin:${PATH}"
    }

    stages {
        stage('Instalar Dependencias (Modo Usuario)') {
            steps {
                script {
                    echo '--- Instalando librerías en ~/.local ---'
                    
                    // 1. Instalar dependencias a nivel de usuario
                    // --user: Instala en el home del usuario (no requiere root)
                    // --break-system-packages: Necesario en Python 3.11+ en Debian/Ubuntu modernos
                    // para permitir instalar sin entorno virtual.
                    sh "pip install --user -r requirements.txt --break-system-packages || pip install --user -r requirements.txt"
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
                    // Usamos "python3 -m uvicorn" que es más robusto para encontrar el módulo
                    // si el PATH a veces falla.
                    sh """
                        nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT} > salida.log 2>&1 &
                    """
                }
            }
        }
    }

    post {
        success {
            echo "¡Despliegue exitoso (Modo Usuario)! API en puerto ${APP_PORT}"
        }
        failure {
            echo "Falló el despliegue. Revisa los logs."
        }
    }
}