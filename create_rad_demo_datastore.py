import dicom
import os
import urllib2
import ssl
import tarfile
import shutil
import uuid
import glob
import pdb

folder_downloaded_datasets = "/rt106/rad_demo_data"
dir_to_process = '/rt106/data'
print "dir_to_process: {}".format(dir_to_process)
os.chdir(folder_downloaded_datasets)

# tarballs and UUIDs to use for each tarball.  Each section of the VH data is NOT is own series, so we will
# create UUIDs for each section so the datastore will treat them as separate series
tarballFiles = ["VHF-Head.tar.gz", "VHF-Shoulder.tar.gz", "VHMCT1mm_Head.tar.gz", "VHMCT1mm_Shoulder.tar.gz"]
tarballUUIDs = {
    "VHF-Head.tar.gz":'2c87ba8b-1bd6-46f6-90b2-c360afbabe4d',
    "VHF-Shoulder.tar.gz": '2bc9d534-ee62-45ad-b5fb-d8fe8dcf5188',
    "VHMCT1mm_Head.tar.gz": '017f45ac-ce32-4921-8700-89d6b0bedb21',
    "VHMCT1mm_Shoulder.tar.gz": 'b806deae-544d-463d-bb88-9cb9814e34fb'
    }


level_2_name = "Patients"
level_4_name = "Primary"
level_5_name = "Imaging"

for tarball in tarballFiles:
    print "extract the tar archive: {}".format(tarball)
    tar = tarfile.open(tarball)
    tar.extractall()
    tar.close()

    subdir = folder_downloaded_datasets
    for p in glob.glob('./*'):
        if os.path.isdir(p):
            print "subdir:{}".format(p)
            subdir = p
            break
    for f in glob.glob(subdir+'/*'):
        print "file path: {}".format(f)
        if os.path.isfile(f):
            break
    One_dicom_file = dicom.read_file(f)

    patientName = One_dicom_file.PatientsName
    studyInstanceUID = One_dicom_file.StudyInstanceUID
    seriesInstanceUID = One_dicom_file.SeriesInstanceUID
    print "From DICOM tags"
    print "patient name : {}".format(patientName)
    print "study ID : {}".format(studyInstanceUID)
    print "series ID : {}".format(seriesInstanceUID)

    # create dir for current patient if not exists
    # use uuid as the series
    seriesUUID = tarballUUIDs[tarball]
    untar_dir = dir_to_process + "/" + level_2_name + "/" + patientName + "/" \
                + level_4_name + "/" + level_5_name + "/" \
                + studyInstanceUID + "/" + seriesUUID
    if not os.path.exists(untar_dir):
        os.makedirs(untar_dir)
    else:
        print "this series has the same patient name, study ID, and series ID"

    for f in glob.glob('./*/*'):
        if os.path.isfile(f):
            shutil.copy(f, untar_dir)
    os.remove(tarball)
    shutil.rmtree(subdir)

shutil.rmtree(folder_downloaded_datasets)
