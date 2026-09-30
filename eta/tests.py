from django.test import TestCase, Client
from django.urls import reverse
import json


class EtaSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_eta_dashboard_loads(self):
        """Verify main SIH 26028 TrackPulse AI dashboard at '/' loads with 200 OK."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TRACKPULSE AI')
        self.assertContains(response, 'PS 26028')
        self.assertContains(response, 'SIMULATED LIVE FEED')

    def test_block_planning_preserved(self):
        """Verify SIH 26027 RailBlock AI preserved at '/block-planning/' loads with 200 OK."""
        response = self.client.get('/block-planning/')
        self.assertEqual(response.status_code, 200)

    def test_api_eta_summary(self):
        """Verify GET /api/eta/ returns valid JSON summary."""
        response = self.client.get('/api/eta/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data_source'], 'SIMULATED LIVE DATA')
        self.assertGreater(len(data['trains']), 0)

    def test_api_eta_train_detail_valid(self):
        """Verify GET /api/eta/train/12931/ returns train forecast details."""
        response = self.client.get('/api/eta/train/12931/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['train_detail']['train_number'], '12931')

    def test_api_eta_train_detail_invalid(self):
        """Verify GET /api/eta/train/99999/ returns clean 404 JSON response."""
        response = self.client.get('/api/eta/train/99999/')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error_code'], 'TRAIN_NOT_FOUND')

    def test_api_simulate_event(self):
        """Verify POST /api/eta/simulate-event/ dynamically updates forecast."""
        payload = {
            'train_number': '12931',
            'event_type': 'ADD_DELAY',
            'delay_minutes': 10,
            'remarks': 'Unit test event'
        }
        response = self.client.post('/api/eta/simulate-event/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_api_reset_simulation(self):
        """Verify POST /api/eta/reset/ resets simulation feed."""
        response = self.client.post('/api/eta/reset/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
