pipeline {
    agent any

    environment {
        TOPSEC_BASE_URL = 'https://10.5.5.5'
        TOPSEC_USERNAME = 'admin'
        TOPSEC_PASSWORD = '1'
    }

    stages {
        // Setup 阶段仅在 requirements.txt 变更或新增依赖时取消注释
        // stage('Setup') {
        //     steps {
        //         sh 'python3 -m pip install -r requirements.txt'
        //         sh 'python3 -m playwright install chromium'
        //     }
        // }

        stage('Test') {
            steps {
                echo '运行测试 (xvfb 虚拟屏幕)...'
                sh 'xvfb-run -a --server-args="-screen 0 1280x1024x24" python3 -m pytest tests/test_yunwei.py -v --headed --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --junitxml=reports/junit.xml'
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
