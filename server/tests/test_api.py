import asyncio
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app, generate_answer
from app.models import ConsultationRequest
from app.vector_store import build_store, search_store

REQUEST = {'category':'임금체불','date':'2026-01-01','amount':'20000','description':'임금 급여 지급이 지연되었습니다','answers':['네']}
# Synthetic records ONLY for unit testing; never shipped as a production corpus.
def record(id='fixture-1',category='임금체불'):
    return {'id':id,'category':category,'title':'테스트용 급여 자료','caseNumber':'TEST-NOT-A-CASE','court':'테스트 법원','judgmentDate':'2026-01-01','summary':'임금 급여 지급 지연 자료 확인 테스트','sourceUrl':'https://www.law.go.kr/precInfoP.do?precSeq=0'}

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        self.env=patch.dict(os.environ,{'CONSULTATION_MODE':'demo','OLLAMA_MODEL':''})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_demo_and_questions(self):
        self.assertEqual(self.client.get('/health').status_code,200)
        self.assertEqual(len(self.client.get('/api/categories').json()['categories']),10)
        self.assertEqual(len(self.client.post('/api/consultations/questions',json=REQUEST).json()['questions']),3)
        data=self.client.post('/api/consultations/result',json=REQUEST).json()
        self.assertEqual(data['summary'],REQUEST['description'])
        self.assertEqual(data['precedents'],[])
        self.assertEqual(data['mode'],'demo')

    def test_validation_does_not_echo_input(self):
        secret='PRIVATE-EXAMPLE'
        response=self.client.post('/api/consultations/result',json={**REQUEST,'category':secret})
        self.assertEqual(response.status_code,422)
        self.assertNotIn(secret,response.text)
        self.assertEqual(self.client.post('/api/consultations/result',json={**REQUEST,'date':'2999-01-01'}).status_code,422)

    def test_missing_index_and_other(self):
        with patch.dict(os.environ,{'CONSULTATION_MODE':'rag','VECTOR_DB_PATH':'/nonexistent/test.sqlite3'}):
            self.assertEqual(self.client.post('/api/consultations/result',json=REQUEST).status_code,503)
            response=self.client.post('/api/consultations/result',json={**REQUEST,'category':'기타'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['precedents'],[])

    def test_index_category_filter_and_retrieval_response(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'index.sqlite3'
            build_store([record(),record('fixture-2','교통사고')],path)
            found=search_store(path,'임금체불','임금 급여 지급 지연')
            self.assertEqual([r['id'] for r in found],['fixture-1'])
            self.assertEqual(search_store(path,'상속','임금 급여 지급'),[])
            self.assertEqual(search_store(path,'기타','임금 급여 지급'),[])
            with patch.dict(os.environ,{'CONSULTATION_MODE':'rag','VECTOR_DB_PATH':str(path)}):
                response=self.client.post('/api/consultations/result',json=REQUEST)
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(response.json()['mode'],'retrieval')
                self.assertEqual(response.json()['precedents'][0]['id'],'fixture-1')

    def test_unknown_model_citations_rejected(self):
        fake=AsyncMock()
        response=unittest.mock.Mock()
        response.json.return_value={'message':{'content':json.dumps({'summary':'예시','citedIds':['invented']})}}
        fake.__aenter__.return_value.post.return_value=response
        with patch.dict(os.environ,{'OLLAMA_MODEL':'test'}),patch('app.main.httpx.AsyncClient',return_value=fake):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(generate_answer(ConsultationRequest(**REQUEST),[record()]))
            self.assertEqual(ctx.exception.status_code,502)

    def test_preprocess_strips_full_body_and_skips_unreviewed(self):
        script=Path(__file__).resolve().parents[2]/'data/scripts/preprocess.py'
        spec=importlib.util.spec_from_file_location('preprocess',script)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            input=Path(folder)/'input.jsonl';output=Path(folder)/'output.jsonl'
            input.write_text(json.dumps({**record(),'reviewed':True,'판례내용':'DO NOT STORE'})+'\n'+json.dumps({**record('skip'),'reviewed':False}),encoding='utf-8')
            module.preprocess([input],output)
            content=output.read_text()
            self.assertNotIn('DO NOT STORE',content)
            self.assertNotIn('skip',content)

if __name__=='__main__':unittest.main()
