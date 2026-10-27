FROM registry.services.nesdis.noaa.gov/ssboxes/science_codes/nos/ioos/hfrnet/process:latest
USER root
RUN groupadd -f -g 1000 hfrnetgroup && useradd -m -u 1000 -N -g 1000 -o hfrnetuser
# Add package updates
RUN set -ex \
  && dnf update -y \
  && dnf clean all \
  && rm -rf /var/cache/yum
COPY --chown=1000:1000 . ./hfrnet
USER hfrnetuser
