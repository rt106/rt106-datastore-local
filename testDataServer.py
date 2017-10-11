# Prototype code for testing dataServer.py

import unittest,json,requests,uuid,tarfile,glob,os,logging
import sys
print(sys.argv)
idx = sys.argv.index('testDataServer.py')
sys.argv = sys.argv[idx:]
print(sys.argv)
from dataServer import app

patientList = ['AGA_260_3','pat001','pat002','pat003','pat004','pat005','pat006']
studyList = ['studyA']
seriesList = ['cardiac_Bias_600_Cardiac_3T_series6_PURE']
imageName = 'i851332.MRDC.1'
slideList = ['AGA_260_3']
regionList = ['021']
channelList = ['DAPI']

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

    def test_bad_request(self):
        url = 'http://localhost:5106/%'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_health_check(self):
        url = 'http://localhost:5106/v1/health'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_health(self):
        url = 'http://localhost:5106/v1'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_get_patient_list(self):
        url = 'http://localhost:5106/api/v1/patients'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        #self.assertTrue(any(json_res))
        patients = [p['patientName'] for p in json_res]
        self.assertEqual(patients, patientList)

    def test_get_study_list(self):
        url = 'http://localhost:5106/api/v1/pat001/study'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        studies = [s['id'] for s in json_res]
        self.assertEqual(studies, studyList)

    def test_get_series_list(self):
        url = 'http://localhost:5106/api/v1/pat001/studyA/series'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertEqual(json_res[0]['id'], seriesList[0])
        #self.assertTrue(any(json_res))

    def test_retrieve_series(self):
        url = 'http://localhost:5106/v1/series/pat001/'+ str(studyList[0]) + '/'+ str(seriesList[0])
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(response.data))

    def test_upload_series(self):
        tar = tarfile.open('/tmp/output.tar','w')
        for f in glob.glob('/test/upload/radiology'):
            filename = os.path.basename(f)
            tar.add(f,arcname=filename)
        tar.close()
        archive = { 'file' : open('/tmp/output.tar' ,'rb') }
        #self.assertEqual(archive, 200)
        url = 'http://localhost:5106/v1/series/pat001/'+ str(studyList[0]) + '/'+ str(seriesList[0])+'_'+ str(uuid.uuid4())+ '/Test_Derived.tar'
        response = self.app.post(url,data=archive)
        self.assertEqual(response.status_code, 200)

    def test_get_series_instance(self):
        url = 'http://localhost:5106/v1/instance/pat001/'+ str(studyList[0]) + '/'+ str(seriesList[0]) + '/' + imageName
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(response.data))

    def test_get_series_metadata(self):
        url = 'http://localhost:5106/v1/series/list/pat001/'+ str(studyList[0]) + '/'+ str(seriesList[0])
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(any(json_res))

    def test_get_annotation(self):
        url = 'http://localhost:5106/v1/annotation/pat001/'+ str(studyList[0]) + '/'+ str(seriesList[0])
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(any(json_res))

    def test_get_slide_list(self):
        url = 'http://localhost:5106/v1/pathology/slide'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertIn(slideList[0], json_res)

    def test_get_slide_regions(self):
        url = 'http://localhost:5106/v1/pathology/' + str(slideList[0]) + '/region'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(any(json_res))

    def test_get_slide_channels(self):
        url = 'http://localhost:5106/v1/pathology/' + str(slideList[0]) + '/' + str(regionList[0]) +'/channel'
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = json.loads(response.data)
        self.assertTrue(any(json_res))

    def test_get_slide_image(self):
        url = 'http://localhost:5106/v1/pathology/image/' + str(slideList[0]) + '/' + str(regionList[0])+'/source/'+ str(channelList[0])
        response = self.app.get(url,content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(response.data))

    # def test_upload_pathology_result(self):
    #     archive = { 'file' : open('/test/upload/pathology/DAPI.tif' ,'rb') }
    #     url = 'http://localhost:5106/v1/pathology/result/'+ str(slideList[0]) + '/' + str(regionList[0])+'/derived/'+ str(channelList[0])
    #     response = self.app.post(url,data=archive)
    #     self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
