ARG BASE_IMAGE=xxx
FROM $BASE_IMAGE
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
# android SDK
############################################
ENV SDK_URL="https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip" \
    ANDROID_HOME="/home/android/.android-sdk" \
    ANDROID_VERSION=28 \
    ANDROID_BUILD_TOOLS_VERSION=27.0.3
RUN mkdir "$ANDROID_HOME" .android \
    && cd "$ANDROID_HOME" \
    && curl -o sdk.zip $SDK_URL \
    && unzip sdk.zip \
    && rm sdk.zip \
    && mkdir "$ANDROID_HOME/licenses" || true \
    && echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > "$ANDROID_HOME/licenses/android-sdk-license"
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
RUN unzip ./android-ndk-r22b-linux-x86_64.zip
WORKDIR /home/android
############################################
RUN git clone https://github.com/oktadev/okta-android-example.git
CMD /bin/bash

