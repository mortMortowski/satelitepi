# Imports
import requests
import os
import predict
import time
from operator import attrgetter
import subprocess
import pyaudio
import wave
import json
import asyncio
import sys
from datetime import datetime

# Global variables

url = "https://celestrak.org/NORAD/elements/weather.txt"
tle_file = "data/tle.txt"
qth = ('51.0671', '-15.3723', 650)
NOAA15 = True
NOAA18 = True
NOAA19 = True
METEOR3 = False
METEOR4 = False

# Functions

def load_settings():
    with open("data/settings.json", "r", encoding="utf-8") as file:
        settings_new = json.load(file)
        
    if not isinstance(settings_new, dict):
        raise ValueError("Settings file must contain a JSON object")
    
    return settings_new

def init_var():
    global url, tle_file, qth, NOAA15, NOAA18, NOAA19, METEOR3, METEOR4
    if settings:
        print("Settings loaded succesfully")
        url = settings.get("url")
        tle_file = settings.get("tle_file")
        latitude = settings.get("latitude")
        longitude = settings.get("longitude")
        altitude = settings.get("altitude")
        qth = (latitude, longitude, altitude)
        NOAA15 = settings.get("satellites")[0].get("record")
        NOAA18 = settings.get("satellites")[1].get("record")
        NOAA19 = settings.get("satellites")[2].get("record")
        METEOR3 = settings.get("satellites")[3].get("record")
        METEOR4 = settings.get("satellites")[4].get("record")
        if (NOAA15 == False and NOAA18 == False and NOAA19 == False and METEOR3 == False and METEOR4 == False):
            print("No satellites selected. Enabling NOAA15 detection so at least one satellite can be recorded.")
            NOAA15 = True
    else:
        print("Couldn't load settings, using default options")
           
settings = load_settings()
init_var()

# INDIVIDUAL TLE DATA
tleNOAA15 = """{0}
{1}
{2}"""
tleNOAA18 = """{0}
{1}
{2}"""
tleNOAA19 = """{0}
{1}
{2}"""
tleMETEOR3 = """{0}
{1}
{2}"""
tleMETEOR4 = """{0}
{1}
{2}"""

# classes
class satellite:
    def __init__(self, name, start, duration, peak, frequency):
        self.name = name
        self.start = start
        self.duration = duration
        self.peak = peak
        self.frequency = frequency

async def get_tle():
    #get tle data
    if(os.path.exists(tle_file)):
        modify_time = os.path.getmtime(tle_file)
        file_age = time.time() - modify_time
        if(file_age > 604800):
            print("Tle file is older than 1 week. Updating tle...")
            # DOWNLOAD TLE DATA ONLY IF FILE IS OLDER THAN 1 WEEK OR DOESN'T EXIST
            response = requests.get(url)
            if(response.status_code == 200):
                print("Downloaded TLE data from server")
                with open(tle_file, "wb") as file:
                    file.write(response.content)
            else:
                print("Cannot connect to server and no TLE data found")
                exit()
        else:
            print("Current tle file will be used")
    else:
        print("No tle file found. Downloading tle...")
        # DOWNLOAD TLE DATA ONLY IF FILE IS OLDER THAN 1 WEEK OR DOESN'T EXIST
        response = requests.get(url)
        if(response.status_code == 200):
            print("Downloaded TLE data from server")
            with open(tle_file, "wb") as file:
                file.write(response.content)
        else:
            print("Cannot connect to server and no TLE data found")
            exit()

    # GET NOAA 15 TLE
    if (NOAA15 == True):
        with open(tle_file, "r", encoding="utf-8") as infile:
            lines = infile.read().splitlines()
            search_string = "NOAA 15"
            i = 0
            global tleNOAA15
            while(i < len(lines)):
                if search_string in lines[i]:
                    tleNOAA15 = tleNOAA15.format(lines[i], lines[i + 1], lines[i + 2])
                    break
                i += 1

    # GET NOAA 18 TLE
    if (NOAA18 == True):
        with open(tle_file, "r", encoding="utf-8") as infile:
            lines = infile.read().splitlines()
            search_string = "NOAA 18"
            i = 0
            global tleNOAA18
            while(i < len(lines)):
                if search_string in lines[i]:
                    tleNOAA18 = tleNOAA18.format(lines[i], lines[i + 1], lines[i + 2])
                    break
                i += 1

    # GET NOAA 19 TLE
    if (NOAA19 == True):
        with open(tle_file, "r", encoding="utf-8") as infile:
            lines = infile.read().splitlines()
            search_string = "NOAA 19"
            i = 0
            global tleNOAA19
            while(i < len(lines)):
                if search_string in lines[i]:
                    tleNOAA19 = tleNOAA19.format(lines[i], lines[i + 1], lines[i + 2])
                    break
                i += 1
                
    # GET METEOR M-2 3 TLE
    if (METEOR3 == True):
        with open(tle_file, "r", encoding="utf-8") as infile:
            lines = infile.read().splitlines()
            search_string = "METEOR-M2 3"
            i = 0
            global tleMETEOR3
            while(i < len(lines)):
                if search_string in lines[i]:
                    tleMETEOR3 = tleMETEOR3.format(lines[i], lines[i+1], lines[i+2])
                    break
                i += 1
                
    # GET METEOR M-2 4 TLE
    if (METEOR4 == True):
        with open(tle_file, "r", encoding="utf-8") as infile:
            lines = infile.read().splitlines()
            search_string = "METEOR-M2 4"
            i = 0
            global tleMETEOR4
            while (i < len(lines)):
                if search_string in lines[i]:
                    tleMETEOR4 = tleMETEOR4.format(lines[i], lines[i+1], lines[i+2])
                    break
                i += 1

async def calculate_pass():
    #calculate pass times
    start_time = time.time()
    
    # GET ALL PASSES IN THE NEXT 12H
    stop_time = time.time() + 43200
    satellites_list = []
    
    if (NOAA15 == True):
        passNOAA15 = predict.transits(tleNOAA15, qth, start_time, stop_time)
    if (NOAA18 == True):
        passNOAA18 = predict.transits(tleNOAA18, qth, start_time, stop_time)
    if (NOAA19 == True):
        passNOAA19 = predict.transits(tleNOAA19, qth, start_time, stop_time)
    if (METEOR3 == True):
        passMETEOR3 = predict.transits(tleMETEOR3, qth, start_time, stop_time)
    if (METEOR4 == True):
        passMETEOR4 = predict.transits(tleMETEOR4, qth, start_time, stop_time)
    
    # transit.peak() for more info

    if (NOAA15 == True):
        for transit in passNOAA15:
            satellites_list.append(satellite("NOAA_15", transit.start, transit.duration(), transit.peak()['elevation'], 137620000))
        
    if (NOAA18 == True):
        for transit in passNOAA18:
            satellites_list.append(satellite("NOAA_18", transit.start, transit.duration(), transit.peak()['elevation'], 137912500))
        
    if (NOAA19 == True):
        for transit in passNOAA19:
            satellites_list.append(satellite("NOAA_19", transit.start, transit.duration(), transit.peak()['elevation'], 137100000))
        
    if (METEOR3 == True):
        for transit in passMETEOR3:
            satellites_list.append(satellite("METEOR-M2_3", transit.start, transit.duration(), transit.peak()['elevation'], 137900000))
        
    if (METEOR4 == True):
        for transit in passMETEOR4:
            satellites_list.append(satellite("METEOR-M2_4", transit.start, transit.duration(), transit.peak()['elevation'], 137900000))
        
    soonest_sat = min(satellites_list, key=attrgetter('start'))
    
    return soonest_sat

async def wait_for_pass(sat):
    #wait for pass
    print("Waiting for pass...")
    time_until = int(sat.start - time.time())
    mins, secs = divmod(time_until, 60)
    timer = '{:02d}:{:02d}'.format(mins, secs)
    print("The next pass will take place in " + timer + " minutes")
    
    if time_until < 0:
        return None
    while time_until:
        time.sleep(1)
        time_until -= 1
    return None

async def record_pass(sat):
    #run rtl sdr
    print(f"Recording {sat.name} pass...")
    
    dt_object = datetime.fromtimestamp(time.time())
    formatted_date = dt_object.strftime("%Y_%m_%d_%H:%M")
    output_file = "recordings/" + str(sat.name) + "_" + formatted_date + ".wav"
    
    success = True
    
    if (sat.name == "NOAA_15" or sat.name == "NOAA_18" or sat.name == "NOAA_19"):
    
        rtl_fm_command = [
            "rtl_fm", "-f", str(sat.frequency), "-M", "-fm", "-s", "60k", "-g", "42.1"
        ]
        
    else:
        
        rtl_fm_command = [
            "rtl_fm", "-f", str(sat.frequency), "-s", "140k", "-g", "42.1"    
        ]
        
    rtl_fm_process = subprocess.Popen(rtl_fm_command, stdout=subprocess.PIPE)
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)
    
    wf = wave.open(output_file, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    
    start_time = time.time()

    try:
        while time.time() - start_time < sat.duration:
            data = await asyncio.to_thread(rtl_fm_process.stdout.read, 1024)
            if not data:
                print("Couldn't open rtl-sdr. Closing the program...")
                success = False
                break
            stream.write(data)
            wf.writeframes(data)
    except Exception as e:
        print("Error during recording: " + str(e))
        success = False
        sys.exit()
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
        rtl_fm_process.terminate()
        rtl_fm_process.stdout.close()
        if (success == True):
            print("Pass recorded")
            return output_file
        else:
            sys.exit()
    
async def process_data(filename):
    #process to images
    print("Processing recorded audio...")
    output_no_ext = filename.replace("recordings/", "").replace(".wav", "")
    output_image = "img/" + output_no_ext + ".png"
    sat_name = output_no_ext[:7]
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"WAV file {filename} does not exist")
    
    if (sat_name == "NOAA_15" or sat_name == "NOAA_18" or sat_name == "NOAA_19"):
    
        image_process_command = [
            "./data/noaa-apt", filename, "-o", output_image   
        ]
        
    else:
        
        image_process_command = [
            "./data/medet_arm", filename, output_image, "-diff", "-q"
        ]
    
    try:
        subprocess.run(image_process_command, check=True)
        print(f"Image saved as {output_image}")
        return output_image
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {filename} into image")
        print("Error: ", e)

async def upload_data(image_path):
    #upload to server
    with open(image_path, "rb") as image_file:
        files = {"file": image_file}
        
        headers = {"Authorization": "some_api_key"} # <-- for the future
        
        try:
            response = requests.post("https://someserver.com/someendpoint", files=files)
            if response.status_code == 200:
                print("Image uploaded successfully")
            else:
                print("Failed to upload image. Status code: ", response.status_code)
            
        except requests.exceptions.Timeout:
            print("The connection timed out")
        except requests.exceptions.TooManyRedirects:
            print("Too many redirects")
        except requests.exceptions.RequestException as e:
            print("Catastrophic error")
            print("Error: ", e)
            
def save_setting(setting, value):
    # Load the JSON file
    with open("data/settings.json", "r", encoding="utf-8") as file:
        obj = json.load(file)
        
    # Handling nested settings
        
    if isinstance(setting, str) and "[" in setting and "]" in setting:
       keys = setting.split(".")
       current = obj
       for key in keys[:-1]:
           if "[" in key and "]" in key:
              list_key, index = key[:-1].split("[")
              index = int(index)
              current = current[list_key][index]
           else:
               current = current[key]
            
       final_key = keys[-1]
       current[final_key] = value
    else:
        # Update flat setting
        obj[setting] = value
    
    # Save the file
            
    with open("data/settings.json", "w", encoding="utf-8") as file:
        json.dump(obj, file, indent=4)
        
    print("Setting saved successfully!")
    
    global settings
    settings = load_settings()
    init_var()

def settings_func():
    #update settings
    print("SETTINGS")
    print("1. Url (", settings.get("url"), ")")
    print("2. tle file (", settings.get("tle_file"), ")")
    print("3. Latitude (", settings.get("latitude"), ")")
    print("4. Longitude (", settings.get("longitude"), ")")
    print("5. Altitude (", settings.get("altitude"), ")")
    print("6. Detect NOAA 15 (", settings.get("satellites")[0].get("record"), ")")
    print("7. Detect NOAA 18 (", settings.get("satellites")[1].get("record"), ")")
    print("8. Detect NOAA 19 (", settings.get("satellites")[2].get("record"), ")")
    print("9. Detect METEOR-M2 3 (", settings.get("satellites")[3].get("record"), ")")
    print("10. Detect METEOR-M2 4 (", settings.get("satellites")[4].get("record"), ")")
    
    selected = input("Choose which setting to change: ")
    
    if (selected == "1"):
        print("Change the url to remote server with tle file in .txt format")
        print("Current setting: ", settings.get("url"))
        print("Default value: https://celestrak.org/NORAD/elements/weather.txt")
        new_setting = input("Enter a new setting or leave blank to not change it: ")
        if (new_setting != ""):
            save_setting("url", new_setting)
            
    elif (selected == "2"):
        print("Change the path to the local tle file in .txt format")
        print("Current setting: ", settings.get("tle_file"))
        print("Default value: data/tle.txt")
        new_setting = input("Enter a new setting or leave blank to not change it: ")
        if (new_setting != ""):
            save_setting("tle_file", new_setting)
            
    elif (selected == "3"):
        print("Change the latitude in format ab.xyzw")
        print("Current setting: ", settings.get("latitude"))
        print("Default setting: 51.0671")
        new_setting = input("Enter a new setting or leave blank to not change it: ")
        if (new_setting != ""):
            save_setting("latitude", new_setting)
            
    elif (selected == "4"):
        print("Change the longitude in format ab.xyzw. Input negative values if calculated pass times are wrong")
        print("Current setting: ", settings.get("longitude"))
        print("Default setting: -15.3723")
        new_setting = input("Enter a new setting or leave blank to not change it: ")
        if (new_setting != ""):
            save_setting("longitude", new_setting)
            
    elif (selected == "5"):
        print("Change the altitude in meters above the sea")
        print("Current setting: ", settings.get("altitude"))
        print("Default setting: 650")
        new_setting = input("Enter a new setting or leave blank to not change it: ")
        if (new_setting != ""):
            save_setting("altitude", new_setting)
            
    elif (selected == "6"):
        if (settings.get("satellites")[0].get("record") == True):
            save_setting("satellites[0].record", False)
        else:
            save_setting("satellites[0].record", True)
            
    elif (selected == "7"):
        if (settings.get("satellites")[1].get("record") == True):
            save_setting("satellites[1].record", False)
        else:
            save_setting("satellites[1].record", True)
                
    elif (selected == "8"):
        if (settings.get("satellites")[2].get("record") == True):
            save_setting("satellites[2].record", False)
        else:
            save_setting("satellites[2].record", True)
            
    elif (selected == "9"):
        if (settings.get("satellites")[3].get("record") == True):
            save_setting("satellites[3].record", False)
        else:
            save_setting("satellites[3].record", True)
            
    elif (selected == "10"):
        if (settings.get("satellites")[4].get("record") == True):
            save_setting("satellites[4].record", False)
        else:
            save_setting("satellites[4].record", True)
            
    else:
        print("Invalid option")

async def main():
    # MENU
    while True:
        print("Welcome to satellitepi!")
        print("1. Start")
        print("2. Settings")
        print("3. Quit")
        
        if len(sys.argv) > 1:
            argument = sys.argv[1]
            selected = argument
        else:
            selected = input("Choose an option: ")

        if (selected == "1"):
            while True:
                await get_tle()
                satellite_obj = await calculate_pass()
                some_value = await wait_for_pass(satellite_obj) # some_value because this function returns None
                pass_wav = await record_pass(satellite_obj)
                image = await process_data(pass_wav)
                #await upload_image(image) disabled because server is not done yet
                
        elif (selected == "2"):
            settings_func()
            
        elif (selected == "3"):
            sys.exit()
            
        else:
            print("Wrong option!")

if __name__ == "__main__":
    asyncio.run(main())
