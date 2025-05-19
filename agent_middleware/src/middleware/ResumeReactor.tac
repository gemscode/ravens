from twisted.application import service
from twisted.internet import reactor
from twisted.python import log
from twisted.web import server, resource
import os
import json
from ResumeProcessor import process_resume

class ProcessEndpoint(resource.Resource):
    isLeaf = True
    
    def render_POST(self, request):
        try:
            data = json.loads(request.content.read())
            folder_id = data['folderId']
            base_path = data['basePath']
            
            resume_service = ResumeProcessorService(base_path)
            reactor.callLater(0, resume_service.process_folder, folder_id)
            
            return json.dumps({"status": "processing"}).encode('utf-8')
        except Exception as e:
            request.setResponseCode(500)
            return json.dumps({"error": str(e)}).encode('utf-8')

class ResumeProcessorService(service.Service):
    def __init__(self, base_path):
        self.base_path = base_path
        
    def process_folder(self, uid):
        try:
            folder_path = os.path.join(self.base_path, uid)
            
            docx_files = [f for f in os.listdir(folder_path) if f.endswith('.docx')]
            if not docx_files:
                log.err(f"No .docx file found in folder {uid}")
                return False
                
            docx_path = os.path.join(folder_path, docx_files[0])
            result = process_resume(docx_path)
            
            output_path = os.path.join(folder_path, 'resume-parsing.json')
            with open(output_path, 'w') as f:
                f.write(result)
            
            self.notify_webapp(uid)
            return True
            
        except Exception as e:
            log.err(f"Error processing folder {uid}: {str(e)}")
            return False
    
    def notify_webapp(self, uid):
        # TODO: Implement notification mechanism (WebSocket/SignalR)
        pass

# Create the application
application = service.Application("ResumeProcessor")

# Create and configure the HTTP endpoint
site = server.Site(ProcessEndpoint())
reactor.listenTCP(9191, site)

# Initialize service with empty base path (will be set per request)
resume_service = ResumeProcessorService("")
resume_service.setServiceParent(application)
