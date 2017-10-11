# Datastore-Local
[![Build Status](http://ideker.crd.ge.com:8888/buildStatus/icon?job=rt106/rt106-datastore-local/master)](http://ideker.crd.ge.com:8888/job/rt106/job/rt106-data-local/job/master/)

Local storage implementation of a Rt 106 datastore.  This is a simple datastore using a directory structure on the filesystem to manage data. This datastore is geared for small, simple deployments. It provides a simple mechanism to wrap or ingest pre-existing data into Rt 106.  The rt106-datastore REST API is used to serve the data to applications and algorithms.

### Local filesystem organization

rt106-datastore-local prescribes a folder structure for data to manage primary (source) data as well as derived data from algorithm executions.

* Patients
    * ```Patient ID``` (or Patient Name)
        * Primary
            * Imaging
                * ```Study ID```
                    * ```Series ID```
                        * ```Image```
                        * ```Image```
                    * ...
                * ...
            * Tables (future)
            * Monitoring (future)
            * Records (future)
        * Results
            * ```Pipeline ID```
                * ```Execution ID```        
                    * Imaging
                        * ```Study ID```
                            * ```Series ID```
                                * ```Image```
                                * ```Image```
                            * ...
                        * ...
                    * Tables (future)
                    * Monitoring (future)
                    * Records (future)
* Slides
    * ```Slide```
        * ```Region```
            * Source
                * ```Channel```
                    * ```Image```
            * ```Pipeline ID```
                * ```Execution ID```
                    * ```Channel```
                        * ```Image```
            * ```Pipeline ID```
                * ```Execution ID```
                    * ```Channel```
                        * ```Image```


ID's may be DICOM UIDs (Study Instance UID) or can be UUIDs.

### Docker container

To build the docker container for the front-end:

    $ docker build -t rt106/rt106-datastore-local:latest .

If you use HTTP proxies in your environment, you may need to build using

    $ docker build -t rt106/rt106-datastore-local:latest  --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy  --build-arg no_proxy=$no_proxy .

### Example radiology data

A sample of the data from the [Visible Human Project](https://www.nlm.nih.gov/research/visible/visible_human.html) can be downloaded and arranged as a local datastore by passing the environment variable ```DOWNLOAD_RAD_DEMO_DATA='on'``` or ```DOWNLOAD_RAD_DEMO_DATA='force'``` to the rt106-datastore-local container on startup.

(DICOM files for Visible Human Project data are downloaded from [https://mri.radiology.uiowa.edu/VHDicom](https://mri.radiology.uiowa.edu/VHDicom).)
