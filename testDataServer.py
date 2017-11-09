# Copyright (c) General Electric Company, 2017.  All rights reserved.

# Prototype code for testing dataServer.py

import unittest,json,requests,uuid,tarfile,glob,os,logging
import sys
print(sys.argv)
idx = sys.argv.index('testDataServer.py')
sys.argv = sys.argv[idx:]
print(sys.argv)
from dataServer import app
import shutil

PATIENT = "Adam"
STUDY = "1.2.826.0.1.3680043.2.1125.1.75064541463040.2005072610175534421"
SERIES = "017f45ac-ce32-4921-8700-89d6b0bedb21"
SERIES_PATH = "/Patients/Adam/Primary/Imaging/"+ STUDY + '/' + SERIES
INSTANCE_PATH = "/Patients/Adam/Primary/Imaging/"+ STUDY + '/' + SERIES + '/' + 'vhm.1001.dcm'
UPLOAD_PATH = '/Patients/'+ PATIENT + '/Results/test_pipeline/test_execid/Imaging/test_study'

class TestDataServerAPIs(unittest.TestCase):

    def setUp(self):       # NOSONAR
        self.app = app.test_client()
        logging.info("start testing dataserver...")

    def tearDown(self):    # NOSONAR
        pass

    def test_not_found(self):
        url = 'http://localhost:5106/invalidinput'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 404)
    
    def test_health_check(self):
        url = 'http://localhost:5106/v1/health'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_health(self):
        url = 'http://localhost:5106/'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_get_patient_list(self):
        url = 'http://localhost:5106/v1/patients'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        patients = [p['id'] for p in json_res]
        self.assertTrue(len(patients) > 0)
        
    def test_get_patient_info(self):
        url = 'http://localhost:5106/v1/patients/' + PATIENT
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        primary_type = json_res['primary']
        self.assertEqual(primary_type[0], 'Imaging')

    def test_get_study_list(self):
        url = 'http://localhost:5106/v1/patients/' + PATIENT + '/imaging/studies'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res[0]['eid'], 'primary')
        
    def test_get_study_type(self):
        url = 'http://localhost:5106/v1/patients/' + PATIENT + '/imaging/studies/' + STUDY + '/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res[0], 'series')
        
    def test_get_primary_series_list(self):
        url = 'http://localhost:5106/v1/patients/' + PATIENT + '/imaging/studies/' + STUDY + '/primary'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res[0]['eid'], 'primary')
        self.assertTrue(len(json_res[0]['id'])>0)
        
    def test_get_series_list(self):
        url = 'http://localhost:5106/v1/patients/' + PATIENT + '/imaging/studies/' + STUDY + '/series'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res[0]['eid'], 'primary')
        self.assertTrue(len(json_res[0]['id'])>0)     
    
    def test_get_series_type(self):
        url = 'http://localhost:5106/v1/series' + SERIES_PATH +'/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_get_image_list(self):
        url = 'http://localhost:5106/v1/series' + SERIES_PATH +'/instances'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(len(json_res['paths'])>0)   
        
    def test_get_uploading_path(self):
        url =  'http://localhost:5106/v1/patients/' + PATIENT + '/results/test_pipeline/steps/test_execid/imaging/studies/test_study/series'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res['path'],UPLOAD_PATH)
     
    def test_retrieve_series(self):
        url = 'http://localhost:5106/v1/series'+ SERIES_PATH + '/archive'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(response.data))
        
    def test_upload_series(self):
        tar = tarfile.open('./output.tar','w')
        for f in glob.glob('/rt106/data' + SERIES_PATH + '/'):
            filename = os.path.basename(f)
            tar.add(f,arcname=filename)
        tar.close()
        archive = { 'file' : open('./output.tar' ,'rb') }
        upload_path = '/uploads/Radiology/test'
        url = 'http://localhost:5106/v1/series' + upload_path + '/tar'
        response = self.app.post(url,data=archive)
        self.assertEqual(response.status_code, 200)
        os.remove('./output.tar')
        shutil.rmtree('/rt106/data' + upload_path)
        shutil.rmtree('/rt106/data/uploads/')
    
    def test_get_instance_type(self):
        url = 'http://localhost:5106/v1/instance' + INSTANCE_PATH +'/type'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res['type'],'DICOM')
    
    def test_get_instance(self):
        url = 'http://localhost:5106/v1/instance' + INSTANCE_PATH +'/DICOM'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(response.data))        
    
    def test_upload_instance(self):
        url = 'http://localhost:5106/v1/instance/uploads/Pathology/test1/tiff16'
        filedir = '/rt106/data/Slides/AGA_260_3/021/Source/DAPI/pERK_CD31_AGA_260_3_S001_P021_dapi.tif'
        shutil.copyfile(filedir, './DAPI.tif')
        archive = { 'file' : open('./DAPI.tif' ,'rb') }    
        response = self.app.post(url,data=archive)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.isfile('/rt106/data/uploads/Pathology/test1/DAPI.tif'))
        shutil.rmtree('/rt106/data/uploads/Pathology/test1/')
        shutil.rmtree('/rt106/data/uploads/')
        
    def test_upload_instance_force(self):
        url = 'http://localhost:5106/v1/instance/uploads/Pathology/test2/tiff16/force'
        filedir = '/rt106/data/Slides/AGA_260_3/021/Source/DAPI/pERK_CD31_AGA_260_3_S001_P021_dapi.tif'
        shutil.copyfile(filedir, './DAPI.tif')
        archive = { 'file' : open('./DAPI.tif' ,'rb') }    
        response = self.app.post(url,data=archive)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.isfile('/rt106/data/uploads/Pathology/test2/DAPI.tif'))
        shutil.rmtree('/rt106/data/uploads/Pathology/test2/')
        shutil.rmtree('/rt106/data/uploads/')

    def test_get_annotation_type(self):
        url = 'http://localhost:5106/v1/annotation' + SERIES_PATH + '/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
    def test_get_annotation(self):
        url = 'http://localhost:5106/v1/annotation' + SERIES_PATH + '/JSON'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(any(json_res))
    
    #
    # Pathology / microscopy section 
    #
        
    def test_get_slide_list(self):
        url = 'http://localhost:5106/v1/pathology/slides'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn("AGA_260_3", json_res)
        
    def test_get_slide_type(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn('regions', json_res)

    def test_get_slide_regions(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn('021', json_res)
        
    def test_get_region_type(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn('channels', json_res)

    def test_get_slide_channels(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/channels'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn('DAPI', json_res)

    def test_get_channel_type(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/channels/DAPI/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual('tiff16', json_res[0])
        
    def test_get_image_path(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/channels/DAPI/image'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(len(json_res[0]) > 0)
        
    def test_get_result_types(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/results/test_pipeline/types'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual('steps', json_res[0])

    def test_get_result_format(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/results/Source/steps/DAPI'
        # need to have the result in the directory to test on
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn('tiff16', json_res)
                
    def test_get_result_path(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/results/Source/steps/DAPI/data'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(len(json_res) > 0)
        
    def test_get_result_image_path(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/results/Source/steps/DAPI/instances'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(len(json_res) > 0)
        
    def test_get_pipeline_list(self):
        url = 'http://localhost:5106/v1/pathology/slides/AGA_260_3/regions/021/results'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
    
    # need to have at least one pipeline available for results    
    #def test_get_execution_list(self):

if __name__ == '__main__':
    unittest.main()
