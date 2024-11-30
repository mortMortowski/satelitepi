# imports
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

# global variables
#settings = load_settings()
#if settings:
#    url = settings.get("url")
#    tle_file = settings.get("tile_file")
#    latitude = settings.get("latitude")
#    longitude = settings.get("longitude")
#    altitude = settings.get("altitude")
#    qth = (latitude, longitude, altitude)
#else: 
url = "https://celestrak.org/NORAD/elements/weather.txt"
tle_file = "tle.txt"
qth = ('51.0671', '-15.3723', 650)

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

async def calculate_pass():
    #calculate pass times
    start_time = time.time()
    
    # GET ALL PASSES IN THE NEXT 12H
    stop_time = time.time() + 43200
    satellites_list = []
    
    passNOAA15 = predict.transits(tleNOAA15, qth, start_time, stop_time)
    passNOAA18 = predict.transits(tleNOAA18, qth, start_time, stop_time)
    passNOAA19 = predict.transits(tleNOAA19, qth, start_time, stop_time)
    
    # transit.peak() for more info

    for transit in passNOAA15:
        satellites_list.append(satellite("NOAA 15", transit.start, transit.duration(), transit.peak()['elevation'], 137620000))
        
    for transit in passNOAA18:
        satellites_list.append(satellite("NOAA 18", transit.start, transit.duration(), transit.peak()['elevation'], 137912500))
        
    for transit in passNOAA19:
        satellites_list.append(satellite("NOAA 19", transit.start, transit.duration(), transit.peak()['elevation'], 137100000))
        
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
    
    rtl_fm_command = [
        "rtl_fm", "-f", str(sat.frequency), "-M", "-fm", "-s", "58k", "-r", "44.1k", "-g", "42.1"
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
        print("Error during recording: " + e)
        success = False
        sys.exit()
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
        rtl_fm_process.terminate()
        #wait asyncio.to_thread(rtl_fm_process.wait)
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
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"WAV file {filename} does not exist")
    
    noaa_apt_command = [
        "./noaa-apt", filename, "-o", output_image   
    ]
    
    try:
        subprocess.run(noaa_apt_command, check=True)
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

def settings():
    #update settings
    print("SETTINGS")
    
def load_settings():
    with open("settings.json", "r", encoding="utf-8") as file:
        settings_new = json.load(file)
    return settings_new

async def main():
    # MENU
    print("Welcome to satellitepi!")
    print("1. Start")
    print("2. Settings")
    print("3. Quit")
    
    if len(sys.argv) > 1:
        argument = sys.argv[1]
        selected = argument
    else:
        selected = input("Choose an option: ")

    if selected == "1":
        while True:
            await get_tle()
            satellite = await calculate_pass()
            some_value = await wait_for_pass(satellite) # some_value because this function returns None
            pass_wav = await record_pass(satellite)
            image = await process_data(pass_wav)
            #await upload_image(image) disabled because server is not done yet
            
    elif selected == "2":
        settings()
        
    elif selected == "3":
        sys.exit()
        
    else:
        print("Wrong option!")

if __name__ == "__main__":
    asyncio.run(main())
