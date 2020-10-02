FROM openjdk:11.0.8-jre-slim-buster

RUN mkdir /GTDCA
COPY config.properties /GTDCA
COPY target/scala-2.13/GroundTDCAdaptor-assembly-0.0.1.jar /GTDCA
WORKDIR /GTDCA

# EXPOSE 224

CMD ["java", "-jar", "GroundTDCAdaptor-assembly-0.0.1.jar"]