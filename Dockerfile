FROM registry.services.nesdis.noaa.gov/ssboxes/science_codes/nos/ioos/hfrnet/process:latest
COPY . ./hfrnet
RUN groupadd -f -g 1000 hfrnetgroup && useradd -m -u 1000 -N -g 1000 -o hfrnetuser
RUN chown -R 1000:1000 ./hfrnet
USER hfrnetuser
