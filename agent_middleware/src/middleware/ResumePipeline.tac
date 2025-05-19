from twisted.application import service
from twisted.internet import reactor
from twisted.python import log
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import json
from ResumeProcessor import process_resume

class ResumeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.docx'):
            try:
                # Process the resume
                result = process_resume(event.src_path)
                
                # Save JSON result
                output_path = os.path.join(os.path.dirname(event.src_path), 'resume-parsing.json')
                with open(output_path, 'w') as f:
                    f.write(result)
                
                # Notify ASP.NET application (implement WebSocket or SignalR notification)
                self.notify_webapp(output_path)
            except Exception as e:
                log.err(f"Error processing resume: {str(e)}")

    def notify_webapp(self, result_path):
        # Implement notification mechanism (WebSocket/SignalR)
        pass

class ResumeMonitorService(service.Service):
    def __init__(self, watch_path):
        self.watch_path = watch_path
        self.observer = None

    def startService(self):
        self.observer = Observer()
        handler = ResumeHandler()
        self.observer.schedule(handler, self.watch_path, recursive=False)
        self.observer.start()
        log.msg(f"Started monitoring {self.watch_path}")

    def stopService(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

# Create the application
application = service.Application("ResumeProcessor")

# Add the resume monitoring service
watch_path = "path/to/upload/directory"
resume_service = ResumeMonitorService(watch_path)
resume_service.setServiceParent(application)
