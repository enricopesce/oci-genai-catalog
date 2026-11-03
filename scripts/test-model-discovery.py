#!/usr/bin/env python3
"""Offline regression checks for discovery export and catalog reconciliation."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('sync_discovery', ROOT / 'scripts/sync-discovery-catalog.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / 'catalog.json').read_text())
        self.model_id = self.catalog['pretrained']['chatModels'][0]['id']
        self.raw = {
            'model-id': self.model_id, 'vendor': 'cohere', 'capabilities': ['CHAT'],
            'api-capability': ['OPENAI_V1_RESPONSES'], 'model-access': 'HOSTED',
            'parameters': [{'name': 'temperature'}],
            'availability': [{'realm': 'oc1', 'region': 'us-ashburn-1',
                              'serving-modes': ['ON_DEMAND'],
                              'time-deprecated': '2027-01-01T00:00:00Z'}]}
        self.matrix = {'metadata': {'generatedAt': '2026-11-03T12:00:00Z'},
                       'modelDiscoveryByRegion': {'us-ashburn-1': {'items': [self.raw]}},
                       'failures': [{'region': 'eu-frankfurt-1', 'query': 'modelDiscovery', 'error': 'denied'}]}

    def test_preserves_documentation_and_reports_disagreements(self):
        original = json.loads(json.dumps(self.catalog))
        result = sync.merge_discovery(self.catalog, self.matrix)
        model = result['pretrained']['chatModels'][0]
        self.assertEqual(model['regions'], self.catalog['pretrained']['chatModels'][0]['regions'])
        self.assertEqual(model['discovery']['regions'], {'us-ashburn-1': 'ondemand'})
        source = result['metadata']['sources']['pretrained']['modelDiscovery']
        self.assertEqual(source['discrepancies'][0]['documented'], 'dedicated')
        self.assertEqual(source['failedQueries'], self.matrix['failures'])
        self.assertEqual(result['pretrained']['discoveryModels'][0]['observations'][0]['model'], self.raw)
        self.assertEqual(self.catalog, original)

    def test_aliases_and_deduplication_preserve_availability_outside_endpoint(self):
        self.catalog['pretrained']['chatModels'][0]['altIds'] = ['test.alias']
        self.raw['model-id'] = 'test.alias'
        self.raw['availability'].append({'realm': 'oc1', 'region': 'sa-saopaulo-1',
                                         'serving-modes': ['DEDICATED', 'ON_DEMAND']})
        self.matrix['modelDiscoveryByRegion']['ap-osaka-1'] = {'items': [self.raw]}
        result = sync.merge_discovery(self.catalog, self.matrix)
        model = result['pretrained']['chatModels'][0]
        self.assertEqual(model['discovery']['regions']['sa-saopaulo-1'], 'both')
        self.assertEqual(model['discovery']['modelIds'], ['test.alias'])
        self.assertEqual(result['metadata']['sources']['pretrained']['modelDiscovery']['unreviewedModelIds'], [])
        observations = result['pretrained']['discoveryModels'][0]['observations']
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]['endpointRegions'], ['ap-osaka-1', 'us-ashburn-1'])

    def test_legacy_inventory_groups_offering_ids_and_excludes_custom_models(self):
        raw = {'display-name': 'test.base', 'id': 'offering1', 'type': 'BASE',
               'vendor': 'test', 'capabilities': ['CHAT'], 'lifecycle-state': 'ACTIVE'}
        self.matrix['regions'] = {'us-ashburn-1': {'items': [raw, dict(raw, id='offering2'),
                                                   dict(raw, type='CUSTOM')]}}
        sync.merge_operational(self.catalog, self.matrix)
        inventory = self.catalog['pretrained']['operationalModels']
        self.assertEqual(len(inventory), 1)
        self.assertEqual(inventory[0]['regionalInventory']['us-ashburn-1']['offeringIds'], ['offering1', 'offering2'])
        self.assertEqual(inventory[0]['lifecycleStates'], ['ACTIVE'])

    def test_empty_success_and_total_failure_are_distinct(self):
        self.matrix['modelDiscoveryByRegion']['us-ashburn-1']['items'] = []
        result = sync.merge_discovery(self.catalog, self.matrix)
        self.assertEqual(result['pretrained']['discoveryModels'], [])
        self.matrix['modelDiscoveryByRegion'] = {}
        with self.assertRaises(ValueError):
            sync.merge_discovery(self.catalog, self.matrix)

    def test_api_case_unknown_models_realms_and_missing_ids(self):
        self.raw.pop('model-id')
        self.raw['modelId'] = 'new.vendor-model'
        self.raw['availability'][0]['realm'] = 'oc2'
        result = sync.merge_discovery(self.catalog, self.matrix)
        self.assertIn('new.vendor-model', result['metadata']['sources']['pretrained']['modelDiscovery']['unreviewedModelIds'])
        self.assertEqual(len(result['pretrained']['chatModels']), len(self.catalog['pretrained']['chatModels']))
        self.raw.pop('modelId')
        with self.assertRaises(ValueError):
            sync.merge_discovery(self.catalog, self.matrix)

    def test_exporter_uses_availability_filter_and_preserves_partial_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            fake = path / 'oci'
            fake.write_text('''#!/usr/bin/env python3
import json,sys
args=sys.argv[1:]
if args[:3]==['iam','region-subscription','list']:
 print(json.dumps({'data':[{'region-name':r,'status':'READY'} for r in ['us-ashburn-1','eu-frankfurt-1','ap-osaka-1','us-phoenix-1']]+[{'region-name':'ignored','status':'IN_PROGRESS'}]}));sys.exit()
region=args[args.index('--region')+1]
if 'list-model-discovery' in args:
 assert args[args.index('--region-parameterconflict')+1]==region
 assert '--all' in args
 if region=='eu-frankfurt-1': print('NotAuthorizedOrNotFound',file=sys.stderr);sys.exit(1)
 if region=='ap-osaka-1': print('{}');sys.exit()
 items=[] if region=='us-phoenix-1' else [{'model-id':'test.model','vendor':'test','capabilities':['CHAT'],'availability':[{'realm':'oc1','region':region,'serving-modes':['ON_DEMAND','DEDICATED']}]}]
 print(json.dumps({'data':{'items':items}}))
elif 'list-models' in args: print(json.dumps({'data':{'items':[]}}))
else: print(json.dumps({'data':[]}))
''')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=str(path) + os.pathsep + os.environ['PATH'])
            output = path / 'matrix.json'
            snapshot = path / 'snapshot.json'
            subprocess.run(['bash', str(ROOT / 'scripts/export-pretrained-model-matrix.sh'),
                            '--compartment-id', 'test', '--tenancy-id', 'test',
                            '--parallel', '2', '--output', str(output), '--catalog-output', str(snapshot)],
                           env=env, check=True, capture_output=True, text=True)
            matrix = json.loads(output.read_text())
            self.assertEqual(len(matrix['metadata']['requestedRegions']), 4)
            self.assertEqual(set(matrix['modelDiscoveryByRegion']), {'us-ashburn-1', 'us-phoenix-1'})
            self.assertEqual(matrix['modelDiscoveryByRegion']['us-phoenix-1']['modelCount'], 0)
            self.assertEqual({f['region'] for f in matrix['failures']}, {'eu-frankfurt-1', 'ap-osaka-1'})
            self.assertTrue(all(f['query'] == 'modelDiscovery' for f in matrix['failures']))
            self.assertEqual(json.loads(snapshot.read_text())['modelDiscoveryByRegion'], matrix['modelDiscoveryByRegion'])


if __name__ == '__main__':
    unittest.main()
