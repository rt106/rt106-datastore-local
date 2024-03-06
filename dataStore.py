# Copyright (c) General Electric Company, 2017.  All rights reserved.

# datastore for local data storage
#
#

import glob, shutil, logging, os, sys, uuid, time
import tarfile, shutil, weakref, threading, hashlib
import json, requests
import boto3, botocore
import pydicom

from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse
from flask import Flask, jsonify, abort, request, make_response, send_file
from flask_cors import CORS, cross_origin

# Uncomment line below for more diagnostic output.
#logging.basicConfig(level=logging.DEBUG)

TEST_ERROR = False

class DataStore:
    def __init__(self):
        self.data_path = os.environ['DATASTORE_LOCAL_DATA_PATH'] if 'DATASTORE_LOCAL_DATA_PATH' in os.environ else '/rt106/data'
        self.weak_refs = dict()

    def authentication(self):
        pass

    def cleanup_once_done(self,response,filepath) :
        wr = weakref.ref(response, self.do_cleanup)
        self.weak_refs[wr] = filepath

    def do_cleanup(self,wr) :
        filepath = self.weak_refs[wr]
        logging.debug('fileremover cleanup - %s' % filepath)
        if os.path.isfile(filepath):
            os.remove(filepath)
        else:
            shutil.rmtree(filepath)

    # Get list of patients.
    def get_patient_list(self):
        logging.debug('get_patient_list()')
        patient_dir =  '%s/Patients' % (self.data_path)
        logging.debug(patient_dir)
        if not os.path.isdir(patient_dir) :
            logging.error('invalid patient_dir - %s' % (patient_dir))
            abort(404)
        patients = []
        for p in glob.glob('%s/*' % patient_dir):
            patients.append( {'patientName':os.path.split(p)[1], 'id':os.path.split(p)[1], 'gender':'m/f', 'birthDate':'unknown'} )
        return make_response(jsonify(patients))

    # Get the type information available for a given patient.
    def get_patient_info(self,patient):
        logging.debug('get_patient_info(), patient=%s' % patient)
        patient_dir =  '%s/Patients/%s' % (self.data_path,patient)
        logging.debug(patient_dir)
        if not os.path.isdir(patient_dir):
            logging.error('invalid patient_dir - %s' % (patient_dir))
            abort(404)

        patient_info = dict()
        primary_types = []
        for p in glob.glob('%s/Primary/*' % patient_dir):
            primary_types.append(os.path.split(p)[1])
        patient_info['primary'] = primary_types

        results_types = dict()
        for p in glob.glob('%s/Results/*' % patient_dir):
            pipeline = os.path.split(p)[1]
            exec_types = dict()
            for e in glob.glob('%s/Results/%s/*' % (patient_dir,pipeline)):
                exec_id = os.path.split(e)[1]
                types = os.listdir(e)
                if len(types) > 0:
                    exec_types[exec_id]  = types
            if len(exec_types) > 0:
                results_types[pipeline] = exec_types
        patient_info['results'] = results_types
        return make_response(jsonify(patient_info))

    # Get list of studies for a given patient ID.
    def get_study_list(self,patient):
        logging.debug('get_study_list(), patient=%s' % patient)
        # Append studies under Primary directory.
        study_dir =  '%s/Patients/%s/Primary/Imaging' % (self.data_path,patient)
        logging.debug(study_dir)

        if TEST_ERROR :
            if 'pat004' in study_dir:    # NOSONAR
                study_dir = study_dir + '_error_test'

        studies = []
        for s in glob.glob('%s/*' % study_dir):
            studies.append( {'id':os.path.split(s)[1],'studyDate':'unknown','eid':'primary','pid':None} )

        # Append studies under Results directory if there is any.
        results_dir = '%s/Patients/%s/Results' % (self.data_path,patient)
        for p in glob.glob('%s/*/*/Imaging/*' % results_dir):
            studies.append({'id':os.path.split(p)[1],'studyDate':'unknown','eid':p.split('/')[-3], 'pid':p.split('/')[-4]})

        if len(studies) < 1:
            logging.error('invalid patient - %s' % (patient))
            abort(404)

        return make_response(jsonify(studies))

    # Get the types of data included in a given study
    def get_study_type(self,patient,study):
        logging.debug('get_study_type(), patient=%s study=%s' % (patient,study))
        series_dir =  '%s/Patients/%s/Primary/Imaging/%s' % (self.data_path,patient,study)
        if not os.path.isdir(series_dir) :
            logging.error('invalid series path - %s' % (series_dir))
            abort(404)
        return make_response(jsonify(['series']))

    # Get list and paths of series for a given patient ID and study ID.
    def get_series_list(self,patient,study):
        logging.debug('get_series_list(), patient=%s  study=%s' % (patient,study))
        # series directories under Primary directory
        series_dir =  '%s/Patients/%s/Primary/Imaging/%s' % (self.data_path,patient,study)
        logging.debug(series_dir)

        if TEST_ERROR :
            if 'pat003' in series_dir:    # NOSONAR
                series_dir = series_dir + '_error_test'

        series = []
        for s in glob.glob('%s/*' % series_dir):
            p = s[(s.find(self.data_path) + len(self.data_path)):]
            series.append( {'id':os.path.split(s)[1],'modality':'unknown','instanceCount':'unknown', 'path':p, 'eid':'primary', 'pid':None} )

        # Append series from Results directory if there is any.
        series_dir =  '%s/Patients/%s/Results/*/*/Imaging/%s' % (self.data_path,patient,study)
        logging.debug(series_dir)
        for s in glob.glob('%s/*' % series_dir):
            p = s[(s.find(self.data_path) + len(self.data_path)):]
            series.append( {'id':os.path.split(s)[1],'modality':'unknown','instanceCount':'unknown', 'path':p, 'eid':s.split('/')[-4], 'pid':s.split('/')[-5] } )

        if len(series) < 1 :
            logging.error('invalid study - %s/%s' % (patient,study))
            abort(404)

        return make_response(jsonify(series))

    # Get the types of data included in a given series
    def get_series_type(self,path):
        logging.debug('get_series_type(), path=%s' % path)
        path = self.data_path + '/' + path
        if not os.path.isdir(path) :
            logging.error('invalid series path - %s' % (path))
            abort(404)

        return make_response(jsonify(['instances','archive']))

    # Get list and paths of primary series for a given patient ID and study ID.
    def get_primary_series_list(self,patient,study):
        logging.debug('get_primary_series_list(), patient=%s  study=%s' % (patient,study))
        # Append series under Primary directory
        series_dir =  '%s/Patients/%s/Primary/Imaging/%s' % (self.data_path,patient,study)
        logging.debug(series_dir)

        if TEST_ERROR :
            if 'pat003' in series_dir:    # NOSONAR
                series_dir = series_dir + '_error_test'

        series = []
        for s in glob.glob('%s/*' % series_dir):
            p = s[(s.find(self.data_path) + len(self.data_path)):]
            series.append( {'id':os.path.split(s)[1],'modality':'unknown','instanceCount':'unknown', 'path':p, 'eid':'primary'} )

        if len(series) < 1 :
            logging.error('invalid study - %s/%s' % (patient,study))
            abort(404)

        return make_response(jsonify(series))

    # Get list of images or data files for a given series path
    def get_image_list(self,path):
        logging.debug('get_image_list(), path of series=%s' % (path))
        path = self.data_path + '/' + path
        if not os.path.isdir(path) :
            logging.error('invalid series path - %s' % (path))
            abort(404)

        files = os.listdir(path)
        paths = []
        for s in glob.glob(path + '/*'):
            p = s[(s.find(self.data_path) + len(self.data_path)):]
            paths.append(p)
        return make_response(jsonify({'files':files, 'paths':paths}))

    # Get the result executions for algorithm or pipeline.
    def get_result_executions(self, patient):
        logging.debug('get_result_executions(), patient=%s' % (patient))

        # Make sure directory structure has: <root>/Patients/<patient>/Results/Executions.  If not, then error.
        exec_dir =  '%s/Patients/%s/Results/Executions' % (self.data_path,patient)
        logging.debug(exec_dir)
        if not os.path.isdir(exec_dir) :
            logging.error('invalid results path - %s' % (exec_dir))
            abort(404)

        # Find the subdirectories under exec_dir and organize these in a JSON structure.
        execids = os.listdir(exec_dir)
        return make_response(jsonify({'execids':execids}))

    # Get the result steps for a pipeline execution.
    def get_result_steps(self, patient, execid):
        logging.debug('get_result_steps(), patient=%s execid=%s' % (patient,execid))

        # Make sure directory structure has: <root>/Patients/<patient>/Results/Executions/<execid>/Step.  If not, then error.
        step_dir =  '%s/Patients/%s/Results/Executions/%s/Step' % (self.data_path,patient,execid)
        logging.debug(step_dir)
        if not os.path.isdir(step_dir) :
            logging.error('invalid results path - %s' % (step_dir))
            abort(404)

        # Find the subdirectories under step_dir and organize these in a JSON structure.
        steps = os.listdir(step_dir)
        return make_response(jsonify({'steps':steps}))

    # Get the result tags for a step in a pipeline execution.
    def get_result_tags(self, patient, execid, step):
        logging.debug('get_result_tags(), patient=%s execid=%s step=%s' % (patient,execid,step))

        # Make sure directory structure has: <root>/Patients/<patient>/Results/Executions/<execid>/Step/<step>/Tag.  If not, then error.
        tag_dir =  '%s/Patients/%s/Results/Executions/%s/Step/%s/Tag' % (self.data_path,patient,execid,step)
        logging.debug(tag_dir)
        if not os.path.isdir(tag_dir) :
            logging.error('invalid results path - %s' % (tag_dir))
            abort(404)

        # Find the subdirectories under tag_dir and organize these in a JSON structure.
        tags = os.listdir(tag_dir)
        return make_response(jsonify({'tags':tags}))

    # Get the result imaging studies within a tag for a step in a pipeline execution.
    def get_result_study(self, patient, execid, step, tag):
        logging.debug('get_result_study(), patient=%s execid=%s step=%s tag=%s' % (patient,execid,step,tag))

        # Make sure directory structure has: <root>/Patients/<patient>/Results/Executions/<execid>/Step/<step>/Tag/<tag>/Imaging.  If not, then error.
        study_dir =  '%s/Patients/%s/Results/Executions/%s/Step/%s/Tag/%s/Imaging' % (self.data_path,patient,execid,step,tag)
        logging.debug(study_dir)
        if not os.path.isdir(study_dir) :
            logging.error('invalid results path - %s' % (study_dir))
            abort(404)

        # Find the subdirectories under study_dir and organize these in a JSON structure.
        studies = os.listdir(study_dir)
        return make_response(jsonify({'studies':studies}))

    # Get the result series within an imaging study for a tag for a step in a pipeline execution.
    def get_result_series(self, patient, execid, step, tag, study):
        logging.debug('get_result_series(), patient=%s execid=%s step=%s tag=%s study=%s' % (patient,execid,step,tag,study))

        # Make sure directory structure has: <root>/Patients/<patient>/Results/Executions/<execid>/Step/<step>/Tag/<tag>/Imaging/<study>.  If not, then error.
        series_dir =  '%s/Patients/%s/Results/Executions/%s/Step/%s/Tag/%s/Imaging/%s' % (self.data_path,patient,execid,step,tag,study)
        logging.debug(series_dir)
        if not os.path.isdir(series_dir) :
            logging.error('invalid results path - %s' % (series_dir))
            abort(404)

        # Find the subdirectories under study_dir and organize these in a JSON structure.
        series = os.listdir(series_dir)
        return make_response(jsonify({'series':series}))

    # Get the path to upload a series
    def get_uploading_path(self,patient,pipeline,execid,study):
       logging.debug('get_uploading_path(), patient=%s pipeline_id=%s exec_id=%s study=%s' % (patient,pipeline,execid,study))
       path = '/Patients/%s/Results/%s/%s/Imaging/%s' % (patient,pipeline,execid,study)
       return make_response(jsonify({'path':path}))

    # Get the path to upload a series
    def get_result_series_path(self,patient,execid,step,tag,study,series):
       logging.debug('get_result_series_path(), patient=%s execid=%s step=%s tag=%s study=%s series=%s' % (patient,execid,step,tag,study,series))
       path = '/Patients/%s/Results/Executions/%s/Step/%s/Tag/%s/Imaging/%s/%s' % (patient,execid,step,tag,study,series)
       return make_response(jsonify({'path':path}))

    # API v2 implementations

    # Get the path for uploading or downloading a patient primary data element

    def get_patient_data_formats(self, patient, exam, element):
        formats_dir = '%s/Patients/%s/Primary/%s/%s' % (self.data_path, patient, exam, element)
        # Get the directories that are under the above directory and return them in a list.
        logging.debug(formats_dir)
        if not os.path.isdir(formats_dir) :
            logging.error('invalid patient exam formats path - %s' % (formats_dir))
            abort(404)
        # Find the subdirectories under study_dir and organize these in a JSON structure.
        formats = os.listdir(formats_dir)
        return make_response(jsonify({'formats':formats}))

    def get_patient_data_path(self,patient,exam,element,format,study='',series=''):
        logging.debug('get_patient_data_path(), patient=%s exam=%s element=%s format=%s' % (patient, exam, element, format))
        format_path = '/Patients/%s/Primary/%s/%s/%s' % (patient, exam, element, format)
        if format.lower() == 'dicom':
            # Return the DICOM series directory, which will be under a study directory.
            # These are passed in as arguments.
            path = format_path + '/%s/%s' % (study,series)
        else:
            # Not DICOM.  The format is nifti or other single-file format.
            path = '' # initialize as empty string
            filename = ''
            # See if there is one file in the path.
            path_contents = os.listdir(self.data_path + format_path)
            if len(path_contents) == 0:
                # If the directory is empty, then path is the same as format_path.
                path = format_path
            elif len(path_contents) == 1:
                # If there is one file in the path, append the filename to the path.
                filename = path_contents[0]
                path = format_path + '/' + filename
                if not os.path.isfile(self.data_path + path):
                    # If the content of the path is not a file, return an error.
                    logging.error('path contains something other than a data file - %s' % (path))
                    abort(404)
            else:
                # There is more than one thing in the path.
                logging.error('path does not contain a single data file - %s' % (path))
                abort(404)
        return make_response(jsonify({'path':path,'filename':filename}))

    # Get the path for uploading or downloading a patient derived data element
    def get_patient_result_top_level_path(self,patient,execid,analytic):
        logging.debug('get_patient_result_top_level_path, patient=%s execid=%s analytic=%s' % (patient, execid, analytic))
        path = '/Patients/%s/Derived/Executions/%s/Analytics/%s/Results' % (patient, execid, analytic)
        return make_response(jsonify({'path': path}))

    def get_patient_result_data_formats(self,patient,execid,analytic,result):
        formats_dir = '%s/Patients/%s/Derived/Executions/%s/Analytics/%s/Results/%s' % (self.data_path, patient, execid, analytic, result)
        # Get the directories that are under the above directory and return them in a list.
        logging.debug(formats_dir)
        if not os.path.isdir(formats_dir) :
            logging.error('invalid patient result formats path - %s' % (formats_dir))
            abort(404)
        # Find the subdirectories under study_dir and organize these in a JSON structure.
        formats = os.listdir(formats_dir)
        return make_response(jsonify({'formats':formats}))

    def get_patient_result_data_path(self,patient,execid,analytic,result,format,study='',series=''):
        logging.debug('get_patient_result_path, patient=%s execid=%s analytic=%s result=%s format=%s' % (patient, execid, analytic, result, format))
        format_path = '/Patients/%s/Derived/Executions/%s/Analytics/%s/Results/%s/%s' % (patient, execid, analytic, result, format)
        if format.lower() == 'dicom':
            # Return the DICOM series directory, which will be under a study directory.
            path = format_path + '/%s/%s' % (study,series)
        else:
            # Not DICOM.  The format is nifti or other single-file format.
            path = '' # initialize as empty string
            filename = ''
            # See if there is one file in the path.
            path_contents = os.listdir(self.data_path + format_path)
            if len(path_contents) == 0:
                # If the directory is empty, then path is the same as format_path.
                path = format_path
            elif len(path_contents) == 1:
                # If there is one file in the path, append the filename to the path.
                filename = path_contents[0]
                path = format_path + '/' + filename
                if not os.path.isfile(self.data_path + path):
                    # If the content of the path is not a file, return an error.
                    logging.error('path contains something other than a data file - %s' % (path))
                    abort(404)
            else:
                # There is more than one thing in the path.
                logging.error('path does not contain a single data file - %s' % (path))
                abort(404)
        return make_response(jsonify({'path':path,'filename':filename}))

    #    def get_uploading_path_pipeline(self,patient,pipeline,step,tag,study,series):
#       logging.debug('get_uploading_path_pipeline(), patient=%s pipeline=%s step=%s tag=%s study=%s series=%s' % (patient,pipeline,step,tag,study,series))
#       path = '/Patients/%s/Results/Pipeline/%s/Step/%s/Tag/%s/Imaging/%s/%s' % (patient,pipeline,step,tag,study,series)
#       return make_response(jsonify({'path':path}))

    # Routine for downloading a series.
    def retrieve_series(self,path,format):
        logging.debug('retrieve_series(), path=%s  format=%s' % (path,format))
        path = self.data_path + '/' + path
        if not os.path.exists(path) :
            logging.error('invalid path - %s' % path)
            abort(404)

        if format != 'archive' and format != 'tar':
            logging.error('invalid format - %s' % format)
            abort(400)

        tmp_tar_path = '/tmp/archive-retrieveSeries-%s.tar' % str(uuid.uuid4())
        logging.debug('creating tempfile - %s ' % tmp_tar_path)

        tmp_tar = tarfile.open(tmp_tar_path,'w')
        for filepath in glob.glob('%s/*' % path) :
            tmp_tar.add(filepath,arcname=os.path.split(filepath)[1])
        tmp_tar.close()

        response =  send_file(tmp_tar_path)
        self.cleanup_once_done(response,tmp_tar_path)
        return response

    # Routine for uploading a series.
    def upload_series(self,upload_path,format):
        upload_path = self.data_path + '/' + upload_path
        logging.debug('upload_series(), path=%s  format=%s' % (upload_path,format))
        if os.path.exists(upload_path) :
            logging.error('path exists already - %s' % upload_path)
            abort(409)

        os.makedirs(upload_path)

        if format != 'tar':
            logging.error('invalid format - %s' % format)
            abort(400)

        tar_filename = upload_path+'/temp.tar'
        file = request.files['file']
        file.save(tar_filename)

        tar = tarfile.open(tar_filename)
        tar.extractall(path=upload_path)
        tar.close()
        os.remove(tar_filename)

        upload_path = upload_path[(upload_path.find(self.data_path) + len(self.data_path)):]
        return make_response(jsonify({'path': upload_path}))

    def upload_series_force(self,upload_path,format):
        upload_path = self.data_path + '/' + upload_path
        logging.info('upload_series_force(), path=%s  format=%s' % (upload_path,format))
        if os.path.exists(upload_path) :
            # Delete contents of the existing upload_path.
            shutil.rmtree(upload_path)
        # Create the upload path if it does not exist.
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        if format != 'tar':
            logging.error('invalid format - %s' % format)
            abort(400)

        tar_filename = upload_path+'/temp.tar'
        file = request.files['file']
        file.save(tar_filename)

        tar = tarfile.open(tar_filename)
        tar.extractall(path=upload_path)
        tar.close()
        os.remove(tar_filename)

        upload_path = upload_path[(upload_path.find(self.data_path) + len(self.data_path)):]
        return make_response(jsonify({'path': upload_path}))

    # Get the type of a given instance, eg, 'tiff16', 'DICOM', 'csv', 'jpeg' etc.
    def get_instance_type(self,path):
        logging.debug('get_instance_type(), path=%s' % path)
        path = self.data_path + '/' + path
        if not os.path.isfile(path) :
            logging.error('invalid instance - %s' %  path)
            abort(404)
        type = None
        supported_types = ['tiff', 'tiff16', 'csv', 'jpeg']
        filename, extension = os.path.splitext(path)
        type = extension[1:].lower()
        if type == 'tif' or type == 'tiff':
            type = 'tiff16'
        elif type not in supported_types:
            type = 'DICOM'
        return make_response(jsonify({'type': type}))

    # Routine for downloading an instance in a series, eg, a DICOM image, or a pathology image.
    def get_instance(self,path,format):
        logging.debug('get_instance(), path=%s  format=%s' % (path,format))
        path = self.data_path + '/' + path
        valid_formats = ['dicom', 'nifti', 'tif', 'tiff', 'tiff16', 'csv', 'npy']
        if format.lower() not in valid_formats:
            logging.error('invalid format - %s' % format)
            abort(400)

        if format.lower() == 'dicom':
            if TEST_ERROR :
                if 'pat002' in path and 'MRDC.5' in path:    # NOSONAR
                    path = path + '.error_test'

        if not os.path.isfile(path) :
            logging.error('invalid instance - %s' %  path)
            abort(404)
        logging.info('datastore sending file %s' % (path))

        return send_file(path)

    # Routine for uploading an instance.
    def upload_instance(self,upload_path,format):
        logging.debug('upload_instance(), path=%s  format=%s' % (upload_path,format))
        # If upload_path includes a file, just take the directory part.
        if not os.path.isfile(upload_path):
            upload_path = os.path.dirname(upload_path)
        upload_path = self.data_path + '/' + upload_path
        # upload_path is merely the directory.  It is OK if it already exists.
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        valid_formats = ['dicom', 'nifti', 'tif', 'tiff', 'tiff16', 'csv', 'npy']
        if format.lower() not in valid_formats:
            logging.error('invalid format - %s' % format)
            abort(400)
        file = request.files['file']
        file_path = '%s/%s' % (upload_path,file.filename)
        if os.path.exists(file_path):
            logging.error('file path already exists and cannot be overwritten - %s' % file_path)
            abort(403)
        file.save(file_path)
        file_path = file_path[(file_path.find(self.data_path) + len(self.data_path)):]
        return make_response(jsonify({'path': file_path}))

    # Routine for uploading an instance.
    def upload_instance_force(self,upload_path,format):
        logging.debug('upload_instance_force(), upload_path=%s  format=%s' % (upload_path,format))
        upload_path = self.data_path + '/' + upload_path
        logging.debug('new upload_path=%s' % upload_path)
        # If upload_path includes a file, just take the directory part.
        if os.path.isfile(upload_path):
            upload_path = os.path.dirname(upload_path)
            logging.debug('modified upload_path=%s' % upload_path)
        else:
            logging.debug('upload_path not modified')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            logging.debug('called os.makedirs()')
        else:
            logging.debug('did not call os.makedirs()')
        valid_formats = ['dicom', 'nifti', 'tif', 'tiff', 'tiff16', 'csv', 'npy']
        if format.lower() not in valid_formats:
            logging.error('invalid format - %s' % format)
            abort(400)
        file = request.files['file']
        file_path = '%s/%s' % (upload_path,file.filename)
        logging.debug('file_path=%s' % file_path)
        if os.path.exists(file_path):
            logging.debug('os.path.exists True')
            # Delete the existing file.
            os.remove(file_path)
            # Make sure the upload path is still there.
            if not os.path.exists(upload_path):
                logging.debug('calling os.makedirs() on %s' % upload_path)
                os.makedirs(upload_path)
            else:
                logging.debug('not calling os.makedirs()')
        else:
            logging.debug('os.path.exists False')
        file.save(file_path)
        file_path = file_path[(file_path.find(self.data_path) + len(self.data_path)):]
        logging.debug('new file_path=%s' % file_path)
        return make_response(jsonify({'path': file_path}))

    def get_annotation_type(self,path):
        logging.debug('get_annotation_type(), path=%s' % path)
        path = self.data_path + '/' + path
        if not os.path.isdir(path) :
            logging.error('invalid series path - %s' % (path))
            abort(404)
        return make_response(jsonify(['JSON','DICOM']))

    def get_annotation_type(self,path):
        logging.debug('get_annotation_type(), path=%s' % path)
        path = self.data_path + '/' + path
        if not os.path.isdir(path) :
            logging.error('invalid series path - %s' % (path))
            abort(404)
        return make_response(jsonify(['JSON','DICOM']))

    # Get Annotation for a series.
    # This initial implementation has one hard-coded response.
    def get_annotation(self,path,format):
        logging.debug('get_annotation(), path=%s  format=%s' % (path,format))

        response = {}
        if format == 'JSON':
            response = {"Comparison": "None. INDICATION",
                  "Indication":"786.50 pt.states has a soreness lt.lower and lateral rib and upper lt.abd.since having a mammogram one month ago.no XXXX or lung complaints.",
                  "Findings": "Chest. Heart size is normal. Pulmonary vasculature is normal. There is a 13 mm nodule in the right lower lobe that is relatively dense, but not obviously calcified on the corresponding rib series. There are probably right hilar calcified lymph XXXX. Lungs otherwise are clear. There is no pleural effusion. Left ribs. No fracture or focal bony destruction.",
                  "Impression":"1. Chest. Large nodule at the right lung base that probably represents a granuloma although not it is not densely calcified. A low KV P chest radiograph can be obtained for confirmation as a there are no comparison studies available in the XXXX. If the patient has an outside chest radiograph, comparison can be XXXX and the report addended. 2. Ribs. Normal. Critical result notification documented through Primordial. If there are questions regarding this interpretation, please XXXX XXXX."}

        # placeholder for annotation on DICOM images
        if format == 'DICOM':    # NOSONAR
            pass

        return make_response(jsonify(response))

    #
    # Pathology / microscopy section
    #
    # Get the list of pathology slides.

    def get_slide_list(self):
        logging.debug('get_slide_list()')
        slide_dir =  '%s/Slides' % (self.data_path)
        logging.debug(slide_dir)
        if not os.path.isdir(slide_dir) :
            logging.error('invalid slide_dir - %s' % (slide_dir))
            abort(404)
        slides = []
        for p in glob.glob('%s/*' % slide_dir):
            slides.append(os.path.split(p)[1])
        return make_response(jsonify(slides))

    # Get the types of data included in a slide.
    def get_slide_type(self,slide):
        logging.debug('get_slide_type(), slide=%s' % slide)
        slide_dir = '%s/Slides/%s' % (self.data_path,slide)
        if not os.path.exists(slide_dir):
            logging.error('invalid path for slide - %s' % (slide))
            abort(404)
        return make_response(jsonify(['regions']))

    # Get the list of regions for a slide.
    def get_slide_regions(self,slide):
        logging.debug('get_slide_regions(), slide=%s' % slide)

        slide_dir = '%s/Slides/%s' % (self.data_path,slide)
        if not os.path.exists(slide_dir):
            logging.error('invalid path for slide - %s' % (slide))
            abort(404)
        # Any junk in the slide_dir will look like microscope slides.
        return make_response(jsonify(os.listdir(slide_dir)))

    # Get the types of data included in a region.
    def get_region_type(self,slide,region):
        logging.debug('get_region_type(), slide=%s region=%s' % (slide,region))
        root_path = '%s/Slides/%s' % (self.data_path,slide)
        if not os.path.exists(root_path):
            logging.error('invalid path for slide - %s' % (slide))
            abort(404)
        return make_response(jsonify(['channels','results']))

    # Get the list of channels for a given slide and a given region.
    def get_slide_channels(self,slide,region):
        logging.debug('get_slide_channels(), slide=%s region=%s' % (slide,region))
        root_path = '%s/Slides/%s' % (self.data_path,slide)
        if not os.path.exists(root_path):
            logging.error('invalid path for slide - %s' % (slide))
            abort(404)
        region_path = '%s/%s' % (root_path,region)
        if not os.path.exists(region_path):
            logging.error('invalid region %s for slide - %s' % (region,slide))
            abort(404)
        data_path = '%s/Source' % (region_path)
        if not os.path.exists(data_path):
            logging.error('invalid source path for region %s for slide - %s' % (region,slide))
            abort(404)
        return make_response(jsonify(os.listdir(data_path)))

    # Get the types of files in a given slide-region-branch-channel
    def get_channel_type(self,slide,region,channel):
        logging.debug('get_image_path(), slide=%s region=%s channel=%s' % (slide,region,channel))
        root_path = '%s/Slides/%s/%s/Source/%s' % (self.data_path,slide,region,channel)
        if not os.path.exists(root_path):
            logging.error('invalid path - %s' % (root_path))
            abort(404)
        return make_response(jsonify(['tiff16']))

    # Get the image path for a given slide-region-branch-channel
    def get_image_path(self,slide,region,channel):
        logging.debug('get_image_path(), slide=%s region=%s channel=%s' % (slide,region,channel))
        root_path = '%s/Slides/%s/%s/Source/%s' % (self.data_path,slide,region,channel)
        if not os.path.exists(root_path):
            logging.error('invalid path - %s' % (root_path))
            abort(404)
        paths = []
        for p in glob.glob(root_path+'/*'):
           if os.path.isfile(p):
               logging.info('get_image_path(), file=%s' % p)
               p = p[(p.find(self.data_path) + len(self.data_path)):]
               paths.append(p)
        return make_response(jsonify(paths))

    # Get the "types" of results with the given pipelineid which for now is literally the string "steps".
    def get_result_types(self,slide,region,pipeline):
        return make_response(jsonify(['steps']))

    # Get the format of the result with given pipelineid and execid
    def get_result_format(self,slide,region,pipelineid,execid):
        logging.debug('get_result_format(), slide=%s region=%s pipelineid=%s execid=%s' % (slide,region,pipelineid,execid))
        root_path = '%s/Slides/%s/%s/%s/%s' % (self.data_path,slide,region,pipelineid,execid)
        if not os.path.exists(root_path):
            logging.error('get_result_format invalid path - %s' % (root_path))
            abort(404)
        types = []
        for p in glob.glob(root_path+'/*'):
            if os.path.isfile(p):
                logging.error('get_result_format(), file=%s' % p)
                filename, extension = os.path.splitext(p)
                type = extension[1:].lower()
                # Need to improve this by determining whether the image is tiff16 vs. tiff.
                if type == 'tif' or type == 'tiff':
                    type = 'tiff16'
                types.append(type)
        return make_response(jsonify(types))

    # Get the path location of the result with given pipelineid and execid
    def get_result_path(self,slide,region,pipelineid,execid):
        logging.debug('get_result_path(), slide=%s region=%s pipelineid=%s execid=%s' % (slide,region,pipelineid,execid))
        path = '/Slides/%s/%s/%s/%s' % (slide,region,pipelineid,execid)
        root_path = '%s%s' % (self.data_path,path)
        if not os.path.exists(root_path):
            # Create the path location if it does not exist.
            os.makedirs(root_path)
        return make_response(jsonify(path))

    # Get the full path with image file names of the result with given pipelineid and execid.
    def get_result_image_path(self, slide, region, pipelineid, execid):
        logging.debug('get_result_image_path(), slide=%s region=%s pipelineid=%s execid=%s' % (slide, region, pipelineid, execid))
        path = '/Slides/%s/%s/%s/%s' % (slide, region, pipelineid, execid)
        root_path = '%s%s' % (self.data_path, path)
        image_paths = []
        for p in glob.glob(root_path + '/*'):
            if os.path.isfile(p):
                p = p[(p.find(self.data_path) + len(self.data_path)):]
                image_paths.append(p)
        return make_response(jsonify(image_paths))

    # Get the image for a given path
    def get_pathology_image(self,path,format):
        logging.debug('get_pathology_image(), path=%s format=%s' % (path,format))
        if not os.path.isfile(path) :
            logging.error('invalid image path - %s' %  path)
            abort(404)
        return send_file(path,format)

    # Get the pipelineid list for a given slide-region
    def get_pipeline_list(self,slide,region):
        logging.debug('get_pipeline_list(), slide=%s region=%s' % (slide,region))
        root_path = '%s/Slides/%s/%s' % (self.data_path,slide,region)
        logging.info('root_path=%s' % root_path)
        if not os.path.exists(root_path) :
            logging.error('get_pipeline_list() invalid path - %s' %  root_path)
            abort(404)
        return make_response(jsonify(os.listdir(root_path)))

    # Get the execid list for a given slide-region-pipeline
    def get_execution_list(self,slide,region,pipeline):
        logging.debug('get_execution_list(), slide=%s region=%s pipeline=%s' % (slide,region,pipeline))
        root_path = '%s/Slides/%s/%s/%s' % (self.data_path,slide,region,pipeline)
        if not os.path.exists(root_path) :
            logging.error('get_exection_list() invalid path - %s' %  root_path)
            abort(404)
        return make_response(jsonify(os.listdir(root_path)))
