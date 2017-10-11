pipeline {
  agent any
  stages {
    stage('scm') {
      steps {
        git(url: 'https://github.build.ge.com/rt106/rt106-datastore-local.git', branch: 'master', changelog: true)
      }
    }
    stage('static') {
      steps {
        withSonarQubeEnv('sonar') {
          script {
            def scannerHome = tool 'sonar'
            sh "${scannerHome}/bin/sonar-scanner"
          }
        }
      }
    }
  }
}
