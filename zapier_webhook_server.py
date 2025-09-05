#!/usr/bin/env python3
"""
Simple HTTP server for Zapier webhooks (no Flask dependency)
Receives Outscraper completion webhooks via Zapier and processes them
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from zapier_webhook_processor import process_zapier_webhook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zapier_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZapierWebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Zapier webhooks"""
    
    def do_GET(self):
        """Handle GET requests - health check and status"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self._send_json_response(200, {
                "status": "healthy",
                "service": "zapier-webhook-server",
                "timestamp": datetime.now().isoformat()
            })
        elif parsed_path.path == '/status':
            self._send_json_response(200, {
                "status": "active",
                "webhook_endpoint": "/webhook/outscraper",
                "health_check": "/health",
                "timestamp": datetime.now().isoformat()
            })
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})
    
    def do_POST(self):
        """Handle POST requests - webhook processing"""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/webhook/outscraper':
                self._handle_outscraper_webhook()
            else:
                self._send_json_response(404, {"error": "Webhook endpoint not found"})
                
        except Exception as e:
            logger.error(f"POST request error: {e}")
            self._send_json_response(500, {"error": f"Internal server error: {str(e)}"})
    
    def _handle_outscraper_webhook(self):
        """Process Outscraper webhook from Zapier"""
        try:
            # Get content length and read body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_json_response(400, {"error": "Empty request body"})
                return
            
            # Read and parse JSON body
            post_data = self.rfile.read(content_length)
            try:
                webhook_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook: {e}")
                self._send_json_response(400, {"error": "Invalid JSON payload"})
                return
            
            logger.info(f"📥 Received webhook from {self.client_address[0]}")
            logger.info(f"Webhook data keys: {list(webhook_data.keys())}")
            
            # Process the webhook using our processor
            result = process_zapier_webhook(webhook_data)
            
            # Return appropriate response based on processing result
            if result["status"] == "success":
                self._send_json_response(200, result)
            elif result["status"] in ["warning", "handled"]:
                self._send_json_response(200, result)
            else:
                self._send_json_response(500, result)
                
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            self._send_json_response(500, {"error": f"Processing failed: {str(e)}"})
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response"""
        response = json.dumps(data, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(response.encode('utf-8'))
        
        # Log the response
        logger.info(f"Response {status_code}: {data.get('message', 'Success')}")
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_server(host='0.0.0.0', port=8000):
    """Run the webhook server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, ZapierWebhookHandler)
    
    logger.info(f"🚀 Starting Zapier webhook server on {host}:{port}")
    logger.info(f"Webhook endpoint: http://{host}:{port}/webhook/outscraper")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"Status check: http://{host}:{port}/status")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
        httpd.shutdown()
        httpd.server_close()

if __name__ == '__main__':
    import sys
    
    # Parse command line arguments
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    run_server(port=port)