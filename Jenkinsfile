pipeline {
    agent any

    environment {
        TOPSEC_BASE_URL = 'https://192.168.3.56'
        TOPSEC_USERNAME = 'admin'
        TOPSEC_PASSWORD = '1'
    }

    stages {
        stage('Setup') {
            steps {
                echo '安装 Python 依赖...'
                bat 'pip install -r requirements.txt'
                echo '安装 Playwright 浏览器...'
                bat 'playwright install chromium'
            }
        }

        stage('Test') {
            steps {
                echo '运行测试...'
                bat '''
                    python -m pytest tests/test_yunwei.py -v ^
                        --html=reports/report.html --self-contained-html ^
                        --alluredir=reports/allure-results ^
                        --junitxml=reports/junit.xml ^
                        --base-url %TOPSEC_BASE_URL%
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    publishHTML(target: [
                        reportName: 'HTML Report',
                        reportDir: 'reports',
                        reportFiles: 'report.html',
                        keepAll: true
                    ])
                    allure includeProperties: false, results: [[path: 'reports/allure-results']]
                    archiveArtifacts artifacts: 'reports/screenshots/**,logs/**.log', fingerprint: true
                }
            }
        }
    }
}
