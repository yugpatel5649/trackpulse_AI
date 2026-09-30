import json
from django.test import TestCase, Client
from eta.models import SimulatedTrain


class EtaSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_eta_dashboard_loads_without_26027_branding(self):
        """Verify main SIH 26028 TrackPulse AI dashboard at '/' loads with 200 OK and contains NO 26027 branding."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Must contain SIH 26028 branding
        self.assertIn('TrackPulse AI', content)
        self.assertIn('PS 26028', content)
        self.assertIn('SIMULATED LIVE DATA', content)
        
        # Must NOT contain 26027 / RailBlock branding on the homepage
        self.assertNotIn('RailBlock AI', content)
        self.assertNotIn('PS 26027', content)
        self.assertNotIn('PS 027', content)
        self.assertNotIn('Block Planning', content)

    def test_block_planning_preserved_at_url(self):
        """Verify SIH 26027 RailBlock AI preserved at '/block-planning/' loads with 200 OK."""
        response = self.client.get('/block-planning/')
        self.assertEqual(response.status_code, 200)

    def test_api_eta_summary(self):
        """Verify GET /api/eta/ returns valid JSON summary from persistent DB."""
        response = self.client.get('/api/eta/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data_source'], 'SIMULATED LIVE DATA')
        self.assertGreater(len(data['trains']), 0)

    def test_backend_state_persistence_across_requests(self):
        """Verify POST simulation event updates database state and survives across GET requests."""
        # Initial delay for train 12931 is 8 min
        t1 = SimulatedTrain.objects.filter(train_number="12931").first()
        initial_delay = t1.current_delay_minutes if t1 else 8

        # Trigger +10 min delay event
        payload = {
            'train_number': '12931',
            'event_type': 'ADD_DELAY',
            'delay_minutes': 10,
            'remarks': 'Persistence unit test'
        }
        post_res = self.client.post('/api/eta/simulate-event/', json.dumps(payload), content_type='application/json')
        self.assertEqual(post_res.status_code, 200)

        # GET /api/eta/ must reflect the updated delay (initial_delay + 10)
        get_res1 = self.client.get('/api/eta/')
        data1 = json.loads(get_res1.content)
        train12931_data1 = next(t for t in data1['trains'] if t['train_number'] == '12931')
        self.assertEqual(train12931_data1['current_delay_minutes'], initial_delay + 10)

        # Subsequent GET request MUST return the exact same modified state from DB
        get_res2 = self.client.get('/api/eta/train/12931/')
        data2 = json.loads(get_res2.content)
        self.assertEqual(data2['train_detail']['current_delay_minutes'], initial_delay + 10)

        # Reset simulation back to baseline
        reset_res = self.client.post('/api/eta/reset/')
        self.assertEqual(reset_res.status_code, 200)

        # Confirm baseline delay restored
        get_res3 = self.client.get('/api/eta/train/12931/')
        data3 = json.loads(get_res3.content)
        self.assertEqual(data3['train_detail']['current_delay_minutes'], 8)

    def test_api_eta_train_detail_invalid(self):
        """Verify GET /api/eta/train/99999/ returns clean 404 JSON response."""
        response = self.client.get('/api/eta/train/99999/')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error_code'], 'TRAIN_NOT_FOUND')
