pipeline {
  agent { docker { image 'python:3.7' } }

  stages {
    stage('test') {
      steps {
        withEnv(["HOME=${env.WORKSPACE}"]) {
          sh 'pip install --user -r devrequirements.txt'
          sh 'python -m unittest discover'
        }
      }
    }
    stage('deploy'){
      agent { docker { image 'nsnow/opsbot-pipeline-env' }} 
      steps{
        withCredentials([
          string(credentialsId: 'harvest-bearer-token', variable: 'BEARER_TOKEN')
        ]) {
          // sh 'gcloud auth activate-service-account --key-file ****'
          // sh 'gcloud config set project ****'
          sh 'gcloud functions deploy harvest_reports --runtime python37 --trigger-http'
        }
      }
    }
  }
}
