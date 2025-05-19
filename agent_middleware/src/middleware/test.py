from ResumeProcessor import process_resume
import json

def test():
    # Specify path to a sample PDF resume
    test_pdf_path = "./TestDocs/test-resume.docx"
    
    # Process the resume
    result = process_resume(test_pdf_path)
    
    # Print results in a formatted way
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test()
