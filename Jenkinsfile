@Library('osirium-pipelines@1.0.0')
import buildPythonEnvironment
import gitCheckout
import pythonEnvironment


def cronString = env.BRANCH_NAME == 'master' ? "0 0 * * *" : ""
def py27env = '/home/osiriumbot/.vcdriver-pyenv27/'
def py35env = '/home/osiriumbot/.vcdriver-pyenv35/'


pipeline {

    agent {
        node 'xenial'
    }

    triggers {
        cron(cronString)
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
        timeout(time: 2, unit: 'HOURS')
    }

    environment {
        vcdriver_test_unix_template = 'Ubuntu-14.04-32bit'
        vcdriver_test_windows_template = 'Windows-Server-2012'
        vcdriver_test_config_file = credentials('osirium-vcdriver-config')
    }

    stages {

        stage('Cleanup') {
            steps {
                gitCheckout 'git@github.com:Osirium/vcdriver.git', env.BRANCH_NAME, env.CHANGE_ID, true, true, false
            }
        }

        stage('Setup') {
            steps {
                parallel(
                    'Python2.7': { buildPythonEnvironment py27env, '/usr/bin/python2.7', 'test_requirements.txt' },
                    'python3.5': { buildPythonEnvironment py35env, '/usr/bin/python3.5', 'test_requirements.txt' }
                )
            }
        }

        stage('Unit Tests') {
            steps {
                parallel(
                    'Python2.7': {
                        dir('test/unit/Python2.7') {
                            pythonEnvironment py27env, 'pytest -v --junitxml=../unit-python-2.7.xml --cov=vcdriver --cov-report html --cov-fail-under 100 ../'
                        }
                    },
                    'python3.5': {
                        dir('test/unit/Python3.5') {
                            pythonEnvironment py35env, 'pytest -v --junitxml=../unit-python-3.5.xml --cov=vcdriver --cov-fail-under 100 ../'
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
                            pythonEnvironment py27env, 'vcdriver_test_folder="Vcdriver Tests Python 2.7" pytest -v -s --junitxml=../integration-python-2.7.xml --cov=vcdriver --cov-report html ../'
                        }
                    },
                    'python3.5': {
                        dir('test/integration/Python3.5') {
                            pythonEnvironment py35env, 'vcdriver_test_folder="Vcdriver Tests Python 3.5" pytest -v -s --junitxml=../integration-python-3.5.xml ../'
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
                pythonEnvironment py27env, 'python setup.py sdist upload -r local'
            }
        }

    }

}
