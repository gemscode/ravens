from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python import log
from twisted.web import server, resource
import os
import json
import sys
from ResumeProcessor import process_resume
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class StringProducer(object):
    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class ProcessEndpoint(resource.Resource):
    isLeaf = True
    
    def render_POST(self, request):
        try:
            data = json.loads(request.content.read())
            folder_id = data['folderId']
            base_path = data['basePath']
            
            resume_service = ResumeProcessorService(base_path)
            reactor.callLater(0, resume_service.process_folder, folder_id)
            
            return json.dumps({"status": "processing"}, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            request.setResponseCode(500)
            return json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8')

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
            
            raw_output_path = os.path.join(folder_path, 'raw-response.txt')
            with open(raw_output_path, 'w', encoding='utf-8') as f:
               f.write(result)
            
            # Remove markdown formatting if present
            cleaned_result = ' '.join(result.split())
            parsed_result = json.loads(cleaned_result)
            
            # Write the cleaned JSON
            output_path = os.path.join(folder_path, 'resume-parsing.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_result, f, ensure_ascii=False, indent=2)
            
            self.notify_webapp(uid)
            return True
           
        except Exception as e:
            log.err(f"Error processing folder {uid}: {str(e)}")
            return False
    
    def notify_webapp(self, uid):
        try:
            from twisted.web.client import Agent, BrowserLikePolicyForHTTPS
            from twisted.web.http_headers import Headers
            from twisted.internet import reactor
            from twisted.internet.ssl import optionsForClientTLS
            from twisted.web.iweb import IPolicyForHTTPS
            from zope.interface import implementer

            @implementer(IPolicyForHTTPS)
            class WebClientPolicy(object):
               def creatorForNetloc(self, hostname, port):
                   return optionsForClientTLS(hostname.decode('ascii'))

            # Create agent with proper HTTPS policy
            agent = Agent(reactor, WebClientPolicy())
        
            # Prepare the notification payload
            body = json.dumps({
                "folderId": uid,
                "status": "completed"
            }, ensure_ascii=False).encode('utf-8')
            
            producer = StringProducer(body)
            
            # Send POST request to the ASP.NET application
            d = agent.request(
                b'POST',
                b'http://localhost:7246/api/ProjectTimeline/processing-complete',
                Headers({b'Content-Type': [b'application/json']}),
                producer
            )
            
            def handle_response(response):
                if response.code == 200:
                    log.msg(f"Successfully notified webapp for folder {uid}")
                else:
                    log.err(f"Failed to notify webapp for folder {uid}")
            
            d.addCallback(handle_response)
            d.addErrback(lambda err: log.err(f"Error notifying webapp: {err}"))
            
        except Exception as e:
            log.err(f"Error in notify_webapp: {str(e)}")

# Create the application
application = service.Application("ResumeProcessor")

# Create and configure the HTTP endpoint
site = server.Site(ProcessEndpoint())
reactor.listenTCP(9191, site)

# Initialize service with empty base path (will be set per request)
resume_service = ResumeProcessorService("")
resume_service.setServiceParent(application)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.run()
