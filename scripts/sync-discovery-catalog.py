#!/usr/bin/env python3
"""Reconcile an authenticated exporter snapshot into catalog.json.

Discovery observations remain separate from documentation-backed presentation
regions. This script never invents descriptive/wizard data for new model IDs.
"""
import argparse
import copy
import json
from pathlib import Path

DISCOVERY_COMMAND = 'OCI CLI generative-ai model-discovery-collection list-model-discovery'
DISCOVERY_URL = 'https://docs.oracle.com/en-us/iaas/api/#/en/generative-ai/20231130/ModelDiscoveryCollection/ListModelDiscovery'


def field(record, name, default=None):
    """Accept OCI CLI kebab-case, API camelCase, and SDK snake_case."""
    parts = name.split('-')
    for key in (name, parts[0] + ''.join(p.title() for p in parts[1:]), name.replace('-', '_')):
        if key in record:
            return record[key]
    return default


def merge_discovery(catalog, matrix):
    result = copy.deepcopy(catalog)
    scans = matrix.get('modelDiscoveryByRegion', {})
    generated = matrix['metadata']['generatedAt']
    if not scans:
        raise ValueError('No successful Model Discovery queries; existing catalog was not changed.')
    models = {}
    for endpoint, scan in sorted(scans.items()):
        for raw in scan['items']:
            model_id = field(raw, 'model-id')
            if not isinstance(model_id, str) or not model_id:
                raise ValueError(f'Discovery response in {endpoint} has no model-id')
            model = models.setdefault(model_id, {'id': model_id, 'observations': []})
            # Preserve each complete response, including unknown/new fields and
            # realm-specific availability. Do not flatten retirements or modes.
            observation = next((o for o in model['observations'] if o['model'] == raw), None)
            if observation is None:
                observation = {'endpointRegions': [], 'model': raw}
                model['observations'].append(observation)
            observation['endpointRegions'].append(endpoint)
    disagreements = []
    presentation = [m for key in ('chatModels', 'embeddingModels', 'rerankModels')
                    for m in result['pretrained'][key]]
    known_ids = {model_id for m in presentation for model_id in [m['id']] + m.get('altIds', [])}
    not_observed = []
    for model in presentation:
        observed = [models[model_id] for model_id in [model['id']] + model.get('altIds', [])
                    if model_id in models]
        if not observed:
            not_observed.append(model['id'])
            continue  # Absence is not proof of retirement or unavailability.
        region_modes = {}
        for observation in [o for m in observed for o in m['observations']]:
            for availability in observation['model'].get('availability') or []:
                region = availability.get('region')
                realm = (availability.get('realm') or '').lower()
                if not region or realm not in ('', 'oc1'):
                    continue
                modes = field(availability, 'serving-modes', []) or []
                region_modes.setdefault(region, set()).update(modes)
        access = {}
        for region, modes in region_modes.items():
            known = modes & {'ON_DEMAND', 'DEDICATED'}
            if known:
                access[region] = ('both' if len(known) == 2 else
                                  'ondemand' if 'ON_DEMAND' in known else 'dedicated')
        model['discovery'] = {'generatedAt': generated, 'modelIds': [m['id'] for m in observed], 'regions': access}
        for region, mode in access.items():
            documented = model.get('regions', {}).get(region)
            if documented != mode:
                disagreements.append({'modelId': model['id'], 'region': region,
                                      'documented': documented, 'discovered': mode})
    source = result['metadata']['sources']['pretrained']
    source['modelDiscovery'] = {
        'status': 'observed', 'generatedAt': generated,
        'officialUrl': DISCOVERY_URL, 'command': DISCOVERY_COMMAND,
        'documentationUrl': 'https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-discovery.htm',
        'successfulRegions': sorted(scans),
        'requestedRegions': matrix['metadata'].get('requestedRegions', sorted(scans)),
        'failedQueries': [f for f in matrix.get('failures', []) if f['query'] == 'modelDiscovery'],
        'observedUniqueModels': len(models),
        'discrepancies': disagreements,
        'unreviewedModelIds': sorted(set(models) - known_ids),
        'notObservedPresentationIds': sorted(not_observed),
        'note': 'Discovery observations validate the official regional table; presentation regions remain documentation-backed. Unreviewed IDs may include fine-tuned/custom models and must be reviewed before publication.',
    }
    result['pretrained']['discoveryModels'] = [models[k] for k in sorted(models)]
    return result


def merge_operational(catalog, matrix):
    """Keep lifecycle/offering IDs from ListModels distinct from discovery."""
    scans = matrix.get('regions', {})
    if not scans:
        return  # Keep the dated last successful inventory if every query failed.
    models = {}
    fields = ['capabilities', 'lifecycle-state', 'lifecycle-details', 'time-created',
              'time-deprecated', 'time-on-demand-retired', 'time-dedicated-retired']
    for region, scan in sorted(scans.items()):
        for raw in scan['items']:
            if raw.get('type') != 'BASE':
                continue  # ListModels also includes tenant custom models.
            model_id = field(raw, 'display-name')
            if not model_id:
                raise ValueError(f'ListModels response in {region} has no display-name')
            model = models.setdefault(model_id, {
                'id': model_id, 'providers': [], 'types': [], 'capabilities': [],
                'longTermSupported': False, 'imageTextToTextSupported': False,
                'observedRegions': [], 'lifecycleStates': [], 'regionalInventory': {},
                'dedicatedClusterMapping': {'status': 'not_exposed_by_cli',
                    'unitShapes': None, 'gpuCount': None,
                    'note': 'Model listings and Limits do not expose model-to-shape or GPU mappings.'}})
            for key, value in [('providers', raw.get('vendor')), ('types', raw.get('type'))]:
                if value and value not in model[key]:
                    model[key].append(value)
            if region not in model['observedRegions']:
                model['observedRegions'].append(region)
            model['longTermSupported'] |= bool(field(raw, 'is-long-term-supported', False))
            model['imageTextToTextSupported'] |= 'IMAGE_TEXT_TO_TEXT' in (raw.get('capabilities') or [])
            inventory = model['regionalInventory'].setdefault(region, {'offeringIds': []})
            if raw.get('id') and raw['id'] not in inventory['offeringIds']:
                inventory['offeringIds'].append(raw['id'])
            for key in fields:
                name = {'lifecycle-state': 'lifecycleStates', 'lifecycle-details': 'lifecycleDetails'}.get(key)
                name = name or key.split('-')[0] + ''.join(p.title() for p in key.split('-')[1:])
                value = field(raw, key)
                values = value if isinstance(value, list) else [value] if value is not None else []
                inventory[name] = sorted(set(inventory.get(name, []) + values))
            model['capabilities'] = sorted(set(model['capabilities'] + (raw.get('capabilities') or [])))
            model['lifecycleStates'] = sorted(set(model['lifecycleStates'] + inventory['lifecycleStates']))
    catalog['pretrained']['operationalModels'] = [models[k] for k in sorted(models)]
    catalog['metadata']['sources']['pretrained']['cliValidation'].update({
        'generatedAt': matrix['metadata']['generatedAt'],
        'successfulRegions': sorted(scans),
        'failedRegions': sorted({f['region'] for f in matrix.get('failures', []) if f['query'] == 'models'}),
        'failedQueries': [{'region': f['region'], 'query': f['query']}
                          for f in matrix.get('failures', []) if f['query'] != 'modelDiscovery'],
        'observedUniqueModels': len(models),
        'limitations': [
            'Legacy ListModels observations supply the operational inventory, offering OCIDs, and lifecycle evidence.',
            'ListModels does not expose context windows, tiers, use-case descriptions, or definitive serving modes. Model Discovery supplies explicit serving modes separately.',
            'regionalInventory records observed lifecycle, not documentation-backed catalog regions.',
            'Limits record tenancy quotas, not model-to-shape compatibility or available capacity.'
        ],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('matrix', type=Path)
    parser.add_argument('--catalog', type=Path, default=Path('catalog.json'))
    parser.add_argument('--output', type=Path, required=True,
                        help='Write a reviewable catalog candidate; does not edit index.html dates.')
    args = parser.parse_args()
    matrix = json.loads(args.matrix.read_text())
    catalog = merge_discovery(json.loads(args.catalog.read_text()), matrix)
    # Preserve previous sizing when a region failed; identify observation dates.
    sizing = catalog['pretrained'].setdefault('clusterSizingByRegion', {})
    prior_date = catalog['metadata']['sources']['pretrained'].get('limitsValidation', {}).get(
        'generatedAt', catalog['metadata']['sources']['pretrained']['cliValidation']['generatedAt'])
    for observation in sizing.values():
        observation.setdefault('observedAt', prior_date)
    for region, observation in matrix.get('clusterSizingByRegion', {}).items():
        sizing[region] = dict(observation, observedAt=matrix['metadata']['generatedAt'])
    merge_operational(catalog, matrix)
    catalog['pretrained']['scanFailures'] = matrix.get('failures', [])
    catalog['metadata']['sources']['pretrained']['limitsValidation'] = {
        'generatedAt': matrix['metadata']['generatedAt'],
        'successfulRegions': sorted(matrix.get('clusterSizingByRegion', {})),
        'note': 'Only successful regions were replaced; other sizing observations retain their previous dates.'}
    args.output.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n')
    print(f'Wrote {args.output}; review discovery discrepancies, new IDs, documentation and UI dates before publishing.')


if __name__ == '__main__':
    main()
