from twisted.application import service
from twisted.internet import reactor
from twisted.python import log
import os
import json
from ResumeProcessor import process_resume

class ResumeProcessorService(service.Service):
    def __init__(self, base_path):
        self.base_path = base_path
        
    def process_folder(self, uid):
        try:
            # Construct folder path using uid
            folder_path = os.path.join(self.base_path, uid)
            
            # Find the first .docx file in the folder
            docx_files = [f for f in os.listdir(folder_path) if f.endswith('.docx')]
            if not docx_files:
                log.err(f"No .docx file found in folder {uid}")
                return False
                
            # Process the resume
            docx_path = os.path.join(folder_path, docx_files[0])
            result = process_resume(docx_path)
            
            # Save result in the same folder
            output_path = os.path.join(folder_path, 'resume-parsing.json')
            with open(output_path, 'w') as f:
                f.write(result)
            
            # TODO: Implement notification to ASP.NET app
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

# Add the resume processing service
base_path = "path/to/base/upload/directory"
resume_service = ResumeProcessorService(base_path)
resume_service.setServiceParent(application)
