import base64
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from generator.service import OpenAIImageError, generate_image_bytes


class GenerateImageBytesTests(SimpleTestCase):
    @patch('generator.service.OPENAI_API_KEY', 'test-key')
    @patch('generator.service.requests.post')
    def test_generate_image_bytes_decodes_base64_response(self, mock_post):
        response = Mock(ok=True)
        response.json.return_value = {
            'data': [{'b64_json': base64.b64encode(b'image-bytes').decode()}]
        }
        mock_post.return_value = response

        result = generate_image_bytes('make a post')

        self.assertEqual(result, b'image-bytes')

    @patch('generator.service.OPENAI_API_KEY', 'test-key')
    @patch('generator.service.requests.post')
    def test_generate_image_bytes_raises_openai_error_body(self, mock_post):
        response = Mock(ok=False, status_code=400)
        response.json.return_value = {'error': {'message': 'Billing hard limit has been reached.'}}
        mock_post.return_value = response

        with self.assertRaisesMessage(OpenAIImageError, 'Billing hard limit'):
            generate_image_bytes('make a post')
