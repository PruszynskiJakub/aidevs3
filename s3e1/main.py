# This is the main entry point for the s3e1 module.

from services import OpenAiService

service = OpenAiService()

def main():
    print("Hello from s3e1!")
    
    # List files from the 'files' directory
    files = list_files('files')
    print("Files in 'files' directory:", files)

if __name__ == "__main__":
    main()
