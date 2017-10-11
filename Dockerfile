FROM rt106/rt106-datastore-api:latest

# install dependencies
USER root
RUN apt-get -y update && apt-get install -y curl

# install datastore code
ADD entrypoint.sh dataStore.py testDataServer.py create_rad_demo_datastore.py download_rad_demo_data.sh /rt106/

# set permissions
RUN chmod a+x /rt106/entrypoint.sh
RUN chmod a+x /rt106/download_rad_demo_data.sh
RUN chown -R rt106:rt106 /rt106

# set the working directory
WORKDIR /rt106

# establish user (created in the base image)
USER rt106:rt106

# configure the default port for the datastore, can be overriden in entrypoint
EXPOSE 5106

# entry point
CMD ["/rt106/entrypoint.sh"]
