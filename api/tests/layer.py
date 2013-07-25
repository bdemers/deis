"""
Unit tests for the Deis api app.

Run the tests with "./manage.py test api"
"""

from __future__ import unicode_literals

import json

from django.test import TestCase


class LayerTest(TestCase):

    """Tests creation of different layers of node types"""

    fixtures = ['tests.json']

    def setUp(self):
        self.assertTrue(
            self.client.login(username='autotest', password='password'))
        url = '/api/providers'
        creds = {'secret_key': 'x'*64, 'access_key': 1*20}
        body = {'id': 'autotest', 'type': 'mock', 'creds': json.dumps(creds)}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        url = '/api/flavors'
        body = {'id': 'autotest', 'provider': 'autotest',
                'params': json.dumps({'region': 'us-west-2', 'instance_size': 'm1.medium'})}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
                
    def test_layer(self):
        """
        Test that a user can create, read, update and delete a node layer
        """
        url = '/api/formations'
        body = {'id': 'autotest', 'flavor': 'autotest'}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        formation_id = response.data['id']
        url = '/api/formations/{formation_id}/layers'.format(**locals())
        body = {'id': 'autotest', 'run_list': 'recipe[deis::test1],recipe[deis::test2]'}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        layer_id = response.data['id']
        self.assertIn('owner', response.data)
        self.assertIn('id', response.data)
        self.assertIn('flavor', response.data)
        self.assertIn('run_list', response.data)
        self.assertIn('image', response.data)
        url = '/api/formations/{formation_id}/layers'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        url = '/api/formations/{formation_id}/layers/{layer_id}'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], layer_id)
        body = {'run_list': 'new'}
        response = self.client.patch(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['run_list'], 'new')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_layer_scale(self):
        url = '/api/formations'
        body = {'id': 'autotest', 'flavor': 'autotest', 'image': 'deis/autotest'}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        formation_id = response.data['id']
        url = '/api/formations/{formation_id}/layers'.format(**locals())
        body = {'id': 'proxy', 'run_list': 'recipe[deis::proxy]'}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        url = '/api/formations/{formation_id}/layers'.format(**locals())
        body = {'id': 'runtime', 'run_list': 'recipe[deis::runtime]'}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        url = '/api/formations/{formation_id}/layers'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # should start with zero
        url = '/api/formations/{formation_id}/nodes'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
        # scale up
        url = '/api/formations/{formation_id}/scale/layers'.format(**locals())
        body = {'proxy': 2, 'runtime': 4}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        url = '/api/formations/{formation_id}/nodes'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 6)
        # scale down
        url = '/api/formations/{formation_id}/scale/layers'.format(**locals())
        body = {'proxy': 1, 'runtime': 2}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        url = '/api/formations/{formation_id}/nodes'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # scale down to 0
        url = '/api/formations/{formation_id}/scale/layers'.format(**locals())
        body = {'proxy': 0, 'runtime': 0}
        response = self.client.post(url, json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        url = '/api/formations/{formation_id}/nodes'.format(**locals())
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)