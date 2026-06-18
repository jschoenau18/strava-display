import stravalib 
from dotenv import load_dotenv, set_key
import os
import time

def api_setup(dotenv_path : str) -> None:

    client_id = int(str(os.getenv(key = "STRAVA_CLIENT_ID")))
    client_secret = str(os.getenv(key = "STRAVA_CLIENT_SECRET"))
    client = stravalib.Client()
    auth_url : str = client.authorization_url(client_id = client_id,
                                          redirect_uri = "http://localhost:8000",
                                          scope = ['profile:read_all', 'activity:read_all'])
    
    print(f"Click the following URL: {auth_url}")
    auth_code = input("Paste the code here:\n")

    token_response = client.exchange_code_for_token(client_id = client_id,
                                                client_secret = client_secret,
                                                code = auth_code,
                                                return_athlete = False)
    # exchange_code_for_token may return an AccessInfo object or a tuple
    # (AccessInfo, SummaryAthlete|None). Normalize to access_info dict-like object.
    if isinstance(token_response, tuple):
        access_info = token_response[0]
    else:
        access_info = token_response
    
    print("✅ Benutzer verbunden!")
    
    # Access fields from AccessInfo attributes
    access_token = getattr(access_info, 'access_token', None) or access_info.get('access_token')
    refresh_token = getattr(access_info, 'refresh_token', None) or access_info.get('refresh_token')
    expires_at = getattr(access_info, 'expires_at', None) or access_info.get('expires_at')

    set_key(dotenv_path, "STRAVA_ACCESS_TOKEN", str(access_token))
    set_key(dotenv_path, "STRAVA_REFRESH_TOKEN", str(refresh_token))
    set_key(dotenv_path, "STRAVA_EXPIRES_AT", str(expires_at))

    print("✅ Tokens erfolgreich in .env gespeichert!")

    client.access_token = access_token
    athlete = client.get_athlete()
    print(f"Erfolgreich verbunden mit dem Profil von: {athlete.firstname} {athlete.lastname}")

def refresh_api_access(dotenv_path : str):

    client = stravalib.Client()
    client_id = int(str(os.getenv("STRAVA_CLIENT_ID")))
    client_secret = str(os.getenv("STRAVA_CLIENT_SECRET"))
    refresh_token = str(os.getenv("STRAVA_REFRESH_TOKEN"))

    token_response = client.refresh_access_token(client_id = client_id,
                                                 client_secret = client_secret,
                                                 refresh_token = refresh_token)
    
    print("✅ Neues Token empfangen!")


    set_key(dotenv_path = dotenv_path,
                key_to_set = "STRAVA_ACCESS_TOKEN",
                value_to_set = token_response.get("access_token"))
        
    set_key(dotenv_path = dotenv_path,
                key_to_set = "STRAVA_EXPIRES_AT",
                value_to_set = str(token_response.get("expires_at")))

    print("✅ Neues Token gespeichert!")

if __name__ == "__main__":

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_dir, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    
    if "STRAVA_EXPIRES_AT" in os.environ:
        print("✅ Benutzer verbunden!")

    else:

        print(f"❌ Kein Konto verbunden. Beginne Setup...")
        api_setup(dotenv_path)
        load_dotenv(dotenv_path=dotenv_path)




    expires_at = os.getenv("STRAVA_EXPIRES_AT")
    if expires_at and int(time.time()) > int(expires_at):

        print("❌ Access Token expired! Refreshe...")
        refresh_api_access(dotenv_path)
        load_dotenv(dotenv_path=dotenv_path)

    else:

        print("✅ Token gültig!")