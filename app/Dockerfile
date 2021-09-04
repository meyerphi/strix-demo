FROM public.ecr.aws/lambda/python:3.8 AS builder

RUN yum -y install git tar patch make gcc gcc-c++ clang clang-libs zlib-devel

# Use build folder to avoid name clashes
RUN mkdir /build
WORKDIR /build

# Build ABC
RUN git clone https://github.com/berkeley-abc/abc
WORKDIR abc
# patch for nicer dot output
COPY abc_remove_titles.patch .
ENV ABC_USE_NO_READLINE=1
RUN patch -p1 < abc_remove_titles.patch && \
    make && \
    cp abc ${LAMBDA_TASK_ROOT}/abc
WORKDIR ..

# Build Spot for autfilt
ENV SPOT_HOME=${LAMBDA_TASK_ROOT}
RUN curl --proto '=https' --tlsv1.2 -sSfL https://www.lrde.epita.fr/dload/spot/spot-2.9.8.tar.gz | tar -xz
WORKDIR spot-2.9.8
RUN ./configure --disable-python --enable-max-accsets=64 --bindir=${SPOT_HOME} --libdir=${SPOT_HOME}/lib --datarootdir=/tmp --includedir=/tmp && \
    make && \
    make install && \
    rm ${SPOT_HOME}/lib/libspotgen.* && \
    rm ${SPOT_HOME}/lib/libspotltsmin.* && \
    rm ${SPOT_HOME}/lib/*.a && \
    strip ${SPOT_HOME}/autfilt && \
    strip ${SPOT_HOME}/lib/*.so
WORKDIR ..

# Install Rust
ENV CARGO_HOME=/cargo
ENV RUSTUP_HOME=/rustup 
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable

# Install GraalVM and native-image
ENV GRAAL_VERSION=21.2.0
ENV GRAAL_FOLDERNAME=graalvm-ce-java11-${GRAAL_VERSION}
ENV GRAAL_FILENAME=graalvm-ce-java11-linux-amd64-${GRAAL_VERSION}.tar.gz
ENV GRAAL_HOME=/graalvm-ce-java11-${GRAAL_VERSION}
ENV JAVA_HOME=/graalvm-ce-java11-${GRAAL_VERSION}
RUN curl --proto '=https' --tlsv1.2 -sSfL https://github.com/graalvm/graalvm-ce-builds/releases/download/vm-${GRAAL_VERSION}/${GRAAL_FILENAME} | tar -xz -C / && \
    ${GRAAL_HOME}/bin/gu install native-image

# Build Strix
RUN git clone https://github.com/meyerphi/strix.git
WORKDIR strix
RUN git submodule init && \
    git submodule update && \
    /cargo/bin/cargo build --release && \
    cp target/release/strix ${LAMBDA_TASK_ROOT}/strix
WORKDIR ..

# Create final container in new stage to minimize size
FROM public.ecr.aws/lambda/python:3.8

# Install strix
COPY --from=builder ${LAMBDA_TASK_ROOT}/strix ${LAMBDA_TASK_ROOT}/

# Install autfilt
COPY --from=builder ${LAMBDA_TASK_ROOT}/autfilt ${LAMBDA_TASK_ROOT}/
COPY --from=builder ${LAMBDA_TASK_ROOT}/lib ${LAMBDA_TASK_ROOT}/lib

# Install ABC
COPY --from=builder ${LAMBDA_TASK_ROOT}/abc ${LAMBDA_TASK_ROOT}/

# Install static version of dot
RUN curl --proto '=https' --tlsv1.2 -sSfL https://github.com/restruct/dot-static/raw/master/x64/dot_static --output ${LAMBDA_TASK_ROOT}/dot && \
    chmod +x ${LAMBDA_TASK_ROOT}/dot

# Copy API code
COPY synthesize.py ${LAMBDA_TASK_ROOT}

# Set lambda handler
CMD [ "synthesize.handler" ]
