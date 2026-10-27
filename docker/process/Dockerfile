FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal AS builder
COPY docker/process/t4_utils-1.0.2a24-py3-none-any.whl /home
COPY conda_environment.yml /home
RUN dnf install -y bzip2 tar && dnf clean all && \
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba && \
    sed -i -e 's/name: .*/name: base/' -e '/^prefix:/d' /home/conda_environment.yml && \
    /bin/micromamba shell init -s bash -r /usr/share/assistt/compilers/micromamba && \
    source ~/.bashrc && \
    micromamba activate && \
    micromamba install -y -f /home/conda_environment.yml && \
    pip install /home/t4_utils-1.0.2a24-py3-none-any.whl && \
    micromamba clean --all --yes
    
FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal
LABEL Maintainer="nesdis.ocs.assistt.cm@noaa.gov"
RUN dnf update -y && \
    dnf install -y wget uuid zip diffutils && dnf clean all && \
    mkdir /home/WORKING_DIR && \
    curl -OL https://truststore.pki.rds.amazonaws.com/us-east-1/us-east-1-bundle.pem && \
    mv us-east-1-bundle.pem /home/WORKING_DIR && \
    chmod 777 /home/WORKING_DIR
    
WORKDIR /home/WORKING_DIR
COPY --from=builder /usr/share/assistt/compilers/micromamba /usr/share/assistt/compilers/micromamba
ENV PATH=/usr/share/assistt/compilers/micromamba/bin:$PATH
USER 1000
