from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python import log
from twisted.web import server, resource
import os
import json
import sys
from MatchingProcessor import calculate_match_percentage, extract_text
from langchain_groq import ChatGroq
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')

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

class MatchEndpoint(resource.Resource):
    isLeaf = True
    
    def render_POST(self, request):
        try:
            data = json.loads(request.content.read())
            resume_path = data['resumePath']
            job_description = data['jobDescription']
            
            match_service = MatchProcessorService()
            reactor.callLater(0, match_service.process_match, resume_path, job_description)
            
            return json.dumps({"status": "processing"}, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            request.setResponseCode(500)
            return json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8')

class MatchProcessorService(service.Service):
    def __init__(self):
        self.chat = ChatGroq(
            api_key=groq_api_key,
            model_name="mixtral-8x7b-32768"
        )
        
    def process_match(self, resume_path, job_description):
        try:
            resume_text = extract_text(resume_path)
            
            if resume_text and job_description:
                match_results = calculate_match_percentage(resume_text, job_description, self.chat)
                self.notify_webapp(match_results)
                return True
            else:
                log.err("Could not extract text from resume or job description is empty.")
                return False
           
        except Exception as e:
            log.err(f"Error processing match: {str(e)}")
            return False
    
    def notify_webapp(self, match_results):
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
            body = json.dumps(match_results, ensure_ascii=False).encode('utf-8')
            
            producer = StringProducer(body)
            
            # Send POST request to the ASP.NET application
            d = agent.request(
                b'POST',
                b'http://localhost:7246/api/matching/matching-complete',
                Headers({b'Content-Type': [b'application/json']}),
                producer
            )
            
            def handle_response(response):
                if response.code == 200:
                    log.msg("Successfully notified webapp with match results")
                else:
                    log.err("Failed to notify webapp with match results")
            
            d.addCallback(handle_response)
            d.addErrback(lambda err: log.err(f"Error notifying webapp: {err}"))
            
        except Exception as e:
            log.err(f"Error in notify_webapp: {str(e)}")

# Create the application
application = service.Application("MatchProcessor")

# Create and configure the HTTP endpoint
site = server.Site(MatchEndpoint())
reactor.listenTCP(9192, site)

# Initialize service
match_service = MatchProcessorService()
match_service.setServiceParent(application)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.run()

