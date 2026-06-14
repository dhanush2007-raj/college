import http.server
import socketserver
import os
import json

PORT = 8000
DIRECTORY = r"c:\Users\dhanu\Downloads\New folder"

class EditorHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Decode HTML data
                html_content = post_data.decode('utf-8')
                
                # Write to the website file directly
                website_path = os.path.join(DIRECTORY, "slvgp-hassan-website.html")
                with open(website_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                # Also save a copy as index.html for web hosting compatibility
                index_path = os.path.join(DIRECTORY, "index.html")
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Saved successfully!"}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def main():
    # Ensure correct working directory
    os.chdir(DIRECTORY)
    
    # Run the TCP HTTP server
    handler = EditorHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("================================================================")
        print("  SLVGP HASSAN LOCAL CMS SERVER RUNNING")
        print("================================================================")
        print(f"  --> Editor Portal: http://localhost:{PORT}/slvgp-hassan-editor.html")
        print(f"  --> Live Website:  http://localhost:{PORT}/slvgp-hassan-website.html")
        print("================================================================")
        print("  Press Ctrl+C in this terminal window to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == '__main__':
    main()
