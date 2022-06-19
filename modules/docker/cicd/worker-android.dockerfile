FROM gradle:5.6.4-jdk8
USER root
# Install Build Essentials
RUN apt-get update && apt-get install build-essential -y && apt-get install file -y && apt-get install apt-utils -y

############################################
# as android user
############################################

RUN useradd -p android -G sudo -ms /bin/bash android
RUN passwd -d android
USER android
ENV USER android
WORKDIR /home/android

############################################
# fetch github key
############################################

RUN mkdir -p ~/.ssh
RUN --mount=type=secret,id=ssh_public,uid=1000 --mount=type=secret,id=ssh_private,uid=1000 ssh-agent bash -c 'ssh-add /run/secrets/ssh_private; ssh-keyscan -H github.com >> ~/.ssh/known_hosts'

############################################

#ADD --chown=android:android "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

############################################
# copy worker implementation files
############################################

ADD --chown=android:android --chmod=700 ci_impl/*.py /home/android/
ADD --chown=android:android --chmod=700 ci_impl/*.sh /home/android/
ADD --chown=android:android --chmod=666 ci_impl/*.svg /home/android/

############################################
# final worker setup
############################################

ADD --chown=android:android worker20.json /home/android/worker.json

ADD --chown=android:android --chmod=700 container-scripts/start-worker.sh /home/android/
ADD --chown=android:android --chmod=700 container-scripts/spin.sh /home/android/
ADD --chown=android:android --chmod=700 container-scripts/worker.bashrc /home/android/.bashrc
ADD --chown=android:android --chmod=700 container-scripts/worker.test.sh /home/android/.worker-test.sh

############################################
# android SDK
############################################

ENV SDK_URL="https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip" \
    ANDROID_HOME="/home/android/.android-sdk" \
    ANDROID_VERSION=28 \
    ANDROID_BUILD_TOOLS_VERSION=27.0.3
# Download Android SDK
RUN mkdir "$ANDROID_HOME" .android \
    && cd "$ANDROID_HOME" \
    && curl -o sdk.zip $SDK_URL \
    && unzip sdk.zip \
    && rm sdk.zip \
    && mkdir "$ANDROID_HOME/licenses" || true \
    && echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_HOME/licenses/android-sdk-license"
#    && yes | $ANDROID_HOME/tools/bin/sdkmanager --licenses
# Install Android Build Tool and Libraries
RUN $ANDROID_HOME/tools/bin/sdkmanager --update
RUN $ANDROID_HOME/tools/bin/sdkmanager "build-tools;${ANDROID_BUILD_TOOLS_VERSION}" \
    "platforms;android-${ANDROID_VERSION}" \
    "platform-tools"


############################################
# android NDK
############################################

RUN mkdir /home/android/.android-ndk-tmp
WORKDIR /home/android/.android-ndk-tmp
RUN wget https://dl.google.com/android/repository/android-ndk-r22b-linux-x86_64.zip
# uncompress
RUN unzip ./android-ndk-r22b-linux-x86_64.zip
#RUN ls ./android-ndk-r22b-linux-x86_64/
# move to it's final location
WORKDIR /home/android
#RUN mv ./.android-ndk-tmp/android-ndk-r22b .android-ndk
# remove temp dir
#RUN rm -rf /home/android/.android-ndk-tmp
# add to PATH
#ENV PATH ${PATH}:${ANDROID_NDK_HOME}

############################################

RUN wget https://sdk.picovr.com/developer-platform/sdk/PicoSDK_Native-2.0.1_B11-20211209.zip
RUN unzip PicoSDK_Native-2.0.1_B11-20211209.zip 

RUN git clone https://github.com/oktadev/okta-android-example.git

CMD /bin/bash

