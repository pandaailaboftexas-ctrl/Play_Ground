import os
import csv
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

def get_authenticated_service():
    # This OAuth 2.0 access scope allows for read-only access to the authenticated
    # user's account, but not other types of account access.
    SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    CLIENT_SECRETS_FILE = 'client_secret.json'
    
    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()
    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_video_comments(service, video_id, output_file):
    # Create a CSV file to store the comments
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        comment_writer = csv.writer(csvfile)
        comment_writer.writerow(['Comment ID', 'Author', 'Published At', 'Updated At', 'Like Count', 'Text'])
        
        # Get comments for the video
        request = service.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100
        )
        
        count = 0
        while request:
            response = request.execute()
            
            for item in response['items']:
                # Process top-level comments
                comment = item['snippet']['topLevelComment']['snippet']
                comment_writer.writerow([
                    item['id'],
                    comment['authorDisplayName'],
                    comment['publishedAt'],
                    comment['updatedAt'],
                    comment['likeCount'],
                    comment['textDisplay']
                ])
                count += 1
                
                # Process replies if any
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        comment_writer.writerow([
                            reply['id'],
                            reply_snippet['authorDisplayName'],
                            reply_snippet['publishedAt'],
                            reply_snippet['updatedAt'],
                            reply_snippet['likeCount'],
                            reply_snippet['textDisplay']
                        ])
                        count += 1
            
            # Check if there are more comments to retrieve
            if 'nextPageToken' in response:
                request = service.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=100
                )
            else:
                break
    
    print(f"Successfully exported {count} comments to {output_file}")

def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    # Get the service object
    service = get_authenticated_service()
    
    # Prompt for the video ID
    video_id = input("Enter YouTube video ID (the part after v= in the URL): ")
    output_file = f"{video_id}_comments.csv"
    
    # Get comments
    get_video_comments(service, video_id, output_file)

if __name__ == "__main__":
    main()