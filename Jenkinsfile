pipeline {
    agent any

    environment {
        TOPSEC_BASE_URL = 'https://10.5.5.5'
        TOPSEC_USERNAME = 'admin'
        TOPSEC_PASSWORD = '1'
    }

    stages {
        stage('Setup') {
            steps {
                echo '安装 Python 依赖...'
                bat '"C:\\Users\\jinpi\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" -m pip install -r requirements.txt'
                echo '安装 Playwright 浏览器...'
                bat '"C:\\Users\\jinpi\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" -m playwright install chromium'
            }
        }

        stage('Test') {
            steps {
                echo '运行测试...'
                bat '"C:\\Users\\jinpi\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" -m pytest tests/test_yunwei.py -v --headed --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --junitxml=reports/junit.xml'
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    archiveArtifacts artifacts: 'reports/screenshots/**,logs/**.log'
                }
            }
        }
    }
}
