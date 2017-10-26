PYTHON_2_7_ENVIRONMENT_PATH = '/home/osiriumbot/.vcdriver-pyenv2/'
PYTHON_3_5_ENVIRONMENT_PATH = '/home/osiriumbot/.vcdriver-pyenv3/'
CRON_STRING = env.BRANCH_NAME == 'master' ? "0 0 * * *" : ""

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
        node 'xenial'
    }

    triggers {
        cron(CRON_STRING)
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
        timeout(time: 2, unit: 'HOURS')
    }

    environment {
        vcdriver_test_unix_template = 'Ubuntu-14.04-32bit'
        vcdriver_test_windows_template = 'Windows-Server-2012'
    }

    stages {

        stage('Cleanup') {
            steps {
                sh 'git reset --hard'
                sh 'git clean -dfx'
            }
        }

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
                    'Python2.7': {
                        dir('test/unit/Python2.7') {
                            withPythonEnvironment(
                                PYTHON_2_7_ENVIRONMENT_PATH,
                                'pytest -v --junitxml=../unit-python-2.7.xml --cov=vcdriver --cov-report html --cov-fail-under 100 ../'
                            )
                        }
                    },
                    'python3.5': {
                        dir('test/unit/Python3.5') {
                            withPythonEnvironment(
                                PYTHON_3_5_ENVIRONMENT_PATH,
                                'pytest -v --junitxml=../unit-python-3.5.xml --cov=vcdriver --cov-fail-under 100 ../'
                            )
                        }
                    }
                )
            }
            post {
                always {
                    publishHTML target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: 'test/unit/Python2.7/htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'UT Coverage'
                    ]
                    junit 'test/unit/unit-python-2.7.xml'
                    junit 'test/unit/unit-python-3.5.xml'
                }
            }
        }

        stage('Integration Tests') {
            steps {
                parallel(
                    'Python2.7': {
                        dir('test/integration/Python2.7') {
                            withVcdriverConfig {
                                withPythonEnvironment(
                                    PYTHON_2_7_ENVIRONMENT_PATH,
                                    'vcdriver_test_folder="Vcdriver Tests Python 2.7" pytest -v -s --junitxml=../integration-python-2.7.xml --cov=vcdriver --cov-report html ../'
                                )
                            }
                        }
                    },
                    'python3.5': {
                        dir('test/integration/Python3.5') {
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
                    publishHTML target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: 'test/integration/Python2.7/htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'IT Coverage'
                    ]
                    junit 'test/integration/integration-python-2.7.xml'
                    junit 'test/integration/integration-python-3.5.xml'
                }
            }
        }

        stage('Build') {
            steps {
                // This relies on the ~/.pypirc config file that setups the repository
                withPythonEnvironment(
                    PYTHON_2_7_ENVIRONMENT_PATH,
                    'python setup.py sdist upload -r local'
                )
            }
        }

    }

}
