PYTHON_2_7_ENVIRONMENT_PATH = '/home/osiriumbot/.vcdriver-pyenv2/'
PYTHON_3_5_ENVIRONMENT_PATH = '/home/osiriumbot/.vcdriver-pyenv3/'

def withPythonEnvironment(path, command) {
    sh '. ' + path + 'bin/activate && ' + command
}

def buildPythonEnvironment(path, interpreter) {
    sh 'virtualenv -p ' + interpreter + ' --clear ' + path
    withPythonEnvironment(path, 'pip install -e .')
    withPythonEnvironment(path, 'pip install pytest pytest-cov mock')
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
                parallel(
                    'Python2.7': { buildPythonEnvironment(PYTHON_2_7_ENVIRONMENT_PATH, '/usr/bin/python2.7') },
                    'python3.5': { buildPythonEnvironment(PYTHON_3_5_ENVIRONMENT_PATH, '/usr/bin/python3.5') }
                )
            }
        }

        stage('Unit Tests) {
            steps {
                parallel(
                    'Python2.7': { withPythonEnvironment(PYTHON_2_7_ENVIRONMENT_PATH, 'pytest -v --junitxml=unit-python-2.7.xml --cov=vcdriver --cov-fail-under 100 test/unit') },
                    'python3.5': { withPythonEnvironment(PYTHON_3_5_ENVIRONMENT_PATH, 'pytest -v --junitxml=unit-python-3.5.xml --cov=vcdriver --cov-fail-under 100 test/unit') }
                )
            }
            post {
                always {
                    junit 'unit-python-2.7.xml'
                    junit 'unit-python-3.5.xml'
                }
            }
        }

        stage('Integration Tests) {
            steps {
                parallel(
                    'Python2.7': { withPythonEnvironment(PYTHON_2_7_ENVIRONMENT_PATH, 'vcdriver_test_folder="Vcdriver Tests Python 2.7" pytest -v -s --junitxml=integration-python-2.7.xml test/integration') },
                    'python3.5': { withPythonEnvironment(PYTHON_3_5_ENVIRONMENT_PATH, 'vcdriver_test_folder="Vcdriver Tests Python 3.5" pytest -v -s --junitxml=integration-python-3.5.xml test/integration') }
                )
            }
            post {
                always {
                    junit 'integration-python-2.7.xml'
                    junit 'integration-python-3.5.xml'
                }
            }
        }

    }

}