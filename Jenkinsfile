PYTHON_2_7_ENVIRONMENT_PATH = '/home/osiriumbot/.vcdriver-pyenv2/'
PYTHON_3_5_ENVIRONMENT_PATH = '/home/osiriumbot/.vcdriver-pyenv3/'

def withPython27Environment(command) {
    sh '. ' + PYTHON_2_7_ENVIRONMENT_PATH + 'bin/activate && ' + command
}

def withPython35Environment(command) {
    sh '. ' + PYTHON_3_5_ENVIRONMENT_PATH + 'bin/activate && ' + command
}

def withVcdriverConfig(body) {
    withCredentials([
        [
            $class: 'FileBinding',
            credentialsId: 'osirium-vcdriver-config',
            variable: 'vcdriver_test_config_file',
        ],
    ], body)
}

pipeline {

    agent {
        node 'ubuntu'
    }

    triggers {
        cron("0 0 * * *")
    }

    environment {
        vcdriver_test_unix_template = 'Ubuntu-14.04-32bit'
        vcdriver_test_windows_template = 'Windows-Server-2012'
    }

    stages {

        stage('Setup') {
            steps {
                sh 'virtualenv -p /usr/bin/python2.7 --clear ' + PYTHON_2_7_ENVIRONMENT_PATH
                withPython27Environment('pip install -e .')
                withPython27Environment('pip install pytest pytest-cov mock')
                sh 'virtualenv -p /usr/bin/python3.5 --clear ' + PYTHON_3_5_ENVIRONMENT_PATH
                withPython35Environment('pip install -e .')
                withPython35Environment('pip install pytest pytest-cov mock')
            }
        }

        stage('Unit Tests Python 2.7.12') {
            steps {
                withPython27Environment('pytest -v --junitxml=unit-python-2.7.12.xml --cov=vcdriver --cov-fail-under 100 test/unit')
            }
            post {
                always {
                    junit 'unit-python-2.7.12.xml'
                }
            }
        }

        stage('Unit Tests Python 3.5.2') {
            steps {
                withPython35Environment('pytest -v --junitxml=unit-python-3.5.2.xml --cov=vcdriver --cov-fail-under 100 test/unit')
            }
            post {
                always {
                    junit 'unit-python-3.5.2.xml'
                }
            }
        }

        stage('Integration Tests Python 2.7.12') {
            steps {
                withVcdriverConfig {
                    withPython27Environment('vcdriver_folder=\'Vcdriver tests\' vcdriver_test_folder=\'Vcdriver tests\' pytest -v -s --junitxml=integration-python-2.7.12.xml test/integration')
                }
            }
            post {
                always {
                    junit 'integration-python-2.7.12.xml'
                }
            }
        }

        stage('Integration Tests Python 3.5.2') {
            steps {
                withVcdriverConfig {
                    withPython35Environment('vcdriver_folder=\'Vcdriver tests\' vcdriver_test_folder=\'Vcdriver tests\' pytest -v -s --junitxml=integration-python-3.5.2.xml test/integration')
                }
            }
            post {
                always {
                    junit 'integration-python-3.5.2.xml'
                }
            }
        }

    }

}