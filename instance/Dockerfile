FROM jenkins/jenkins:lts

USER root

# Установка необходимых пакетов
RUN apt-get update && \
    apt-get -y install apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    software-properties-common

# Добавление ключа Docker GPG
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

# Добавление репозитория Docker
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"

# Установка Docker
RUN apt-get update && \
    apt-get -y install docker-ce docker-ce-cli containerd.io

# Добавление пользователя jenkins в группу docker
RUN usermod -aG docker jenkins

USER jenkins