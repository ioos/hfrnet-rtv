FROM redhat/ubi9
LABEL Maintainer="nesdis.ocs.assistt.cm@noaa.gov"
COPY docker/process/t4_utils-1.0.2a23-py3-none-any.whl /home
COPY conda_environment.yml /home/
ENV PATH=/usr/share/assistt/compilers/miniconda3/bin:$PATH
ENV CONDA_AUTO_UPDATE_CONDA=false
RUN dnf update -y && \
    dnf install -y wget uuid zip diffutils && \
    rpm -ivh https://mirror.stream.centos.org/9-stream/AppStream/x86_64/os/Packages/ksh-1.0.6-3.el9.x86_64.rpm && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-py39_24.1.2-0-Linux-x86_64.sh && \
    bash Miniconda3-py39_24.1.2-0-Linux-x86_64.sh -b -p /usr/share/assistt/compilers/miniconda3 && \
    rm Miniconda3-py39_24.1.2-0-Linux-x86_64.sh && \
    sed -i -e 's/name: .*/name: base/' -e '/^prefix:/d' /home/conda_environment.yml && \
    conda env update --file /home/conda_environment.yml && \
    pip install /home/t4_utils-1.0.2a23-py3-none-any.whl && \
    rm /home/conda_environment.yml && \
    rm /home/t4_utils-1.0.2a23-py3-none-any.whl && \
    mkdir /home/WORKING_DIR && \
    chmod 777 /home/WORKING_DIR
WORKDIR /home/WORKING_DIR
