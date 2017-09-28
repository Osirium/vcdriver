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

        stage('Unit Tests') {
            steps {
                parallel(
                    'Python2.7': { withPythonEnvironment(PYTHON_2_7_ENVIRONMENT_PATH, 'pytest -v --junitxml=testing/unit/unit-python-2.7.xml --cov=vcdriver --cov-fail-under 100 test/unit') },
                    'python3.5': { withPythonEnvironment(PYTHON_3_5_ENVIRONMENT_PATH, 'pytest -v --junitxml=testing/unit/unit-python-3.5.xml --cov=vcdriver --cov-fail-under 100 test/unit') }
                )
            }
            post {
                always {
                    junit 'testing/unit/unit-python-2.7.xml'
                    junit 'testing/unit/unit-python-3.5.xml'
                }
            }
        }

        stage('Integration Tests') {
            steps {
                parallel(
                    'Python2.7': {
                        dir('testing/integration/Python2.7') {
                            withVcdriverConfig {
                                withPythonEnvironment(
                                    PYTHON_2_7_ENVIRONMENT_PATH,
                                    'vcdriver_test_folder="Vcdriver Tests Python 2.7" pytest -v -s --junitxml=../integration-python-2.7.xml ../'
                                )
                            }
                        }
                    },
                    'python3.5': {
                        dir('testing/integration/Python3.5') {
                            withVcdriverConfig {
                                withPythonEnvironment(
                                    PYTHON_3_5_ENVIRONMENT_PATH,
                                    'vcdriver_test_folder="Vcdriver Tests Python 3.5" pytest -v -s --junitxml=../integration-python-3.5.xml ../'
                                )
                            }
                        }
                    }
                )
            }
            post {
                always {
                    junit 'testing/integration/integration-python-2.7.xml'
                    junit 'testing/integration/integration-python-3.5.xml'
                }
            }
        }

    }

}