import network
import socket
import machine
import re
import time
import json
import ntptime
import uasyncio # to cancel server

# Captive Portal
from phew import server, template, access_point, dns, logging
from phew.template import render_template
from phew.server import redirect

# This is the address that is shown on the Captive Portal
DOMAIN = "bird.friend"
DEFAULT_HOSTNAME = "🐦"
DEFAULT_PASSWORD = "birdfriend"


def start_access_point():
    global bird_ap
    bird_ap = access_point(DEFAULT_HOSTNAME, DEFAULT_PASSWORD)
    ip = bird_ap.ifconfig()[0]
    # Grab the IP address and store it
    logging.info(f"starting DNS server on {ip}")
    # # Catch all requests and reroute them
    dns.run_catchall(ip)
    server.run() # Runs the server as part of uasyncio continuous loop

def stop_access_point():
    logging.info(f"Stopping Access point")
    # can't cancel self?
    # uasyncio.current_task().cancel()
    bird_ap.active(False)
    time.sleep(2) # takes a moment for AP to stop
    logging.info(f"bird_ap Access point Active? {bird_ap.active()}")


def load_data(data_file="data.json"):
    try:
        data = open(data_file)
        json_data = json.loads(data.read())
        ssid = json_data["ssid"]
        password = json_data["password"]
        local_time = json_data["local_time"]
        earliest = json_data["earliest"]
        latest = json_data["latest"]
        interval = json_data["interval"]
        return { "ssid": ssid,
                "password": password,
                "local_time": local_time,
                "earliest": earliest,
                "latest": latest,
                "interval": interval
                }
    except Exception as e:
        return {}

def write_data(form):
    json_form_data = json.dumps({
        'ssid': form.get("ssid", ""),
        'password': form.get("password", ""),
        'local_time': form.get("localTime", ""),
        'earliest': form.get("earliest", ""),
        'latest': form.get("latest", ""),
        'interval': form.get("interval", "")
    })
    # Writing to sample.json
    with open("data.json", "w") as outfile:
        outfile.write(json_form_data)
    return True

def time_str():
    t = time.localtime()
    return f"{t[0]}/{t[1]}/{t[2]} {t[3]}:{t[4]}"

# accepts string like 2023-01-09T22:41
def set_time():
    time_str = load_data()['local_time']
    year = int(time_str[0:4])
    month = int(time_str[5:7])
    day = int(time_str[8:10])
    hour = int(time_str[11:13])
    min = int(time_str[14:16])
    # (year, month, day, weekday, hours, minutes, seconds, subseconds)
    tup = (year, month, day, 0, hour, min, 0, 0)
    machine.RTC().datetime(tup)
    return True

# === Server endpoints ===
#
@server.route("/", methods=['GET'])
def index(request):
    if request.method == 'GET':
        return render_template("src/index.html")

@server.route("/data", methods=["POST"])
def data_form(request):
    if write_data(request.form) and set_time():
        data = load_data()
        earliest = data['earliest']
        latest = data['latest']
        interval = data['interval']
        return render_template("src/reset.html", local_time=time_str(), earliest=earliest, latest=latest, interval=interval)
    else:
        return render_template("src/index.html", error="error saving")

@server.route("/disable", methods=["GET"])
def disable(request):
    if request.method == "GET":
        logging.info("disable access pt")
        stop_access_point()

@server.route("/wrong-host-redirect", methods=["GET"])
def wrong_host_redirect(request):
  # if the client requested a resource at the wrong host then present
  # a meta redirect so that the captive portal browser can be sent to the correct location
  body = "<!DOCTYPE html><head><meta http-equiv=\"refresh\" content=\"0;URL='http://" + DOMAIN + "'/ /></head>"
  logging.debug("body:",body)
  return body

@server.route("/hotspot-detect.html", methods=["GET"])
def hotspot(request):
    """ Redirect to the Index Page """
    return render_template("src/index.html")

@server.catchall()
def catch_all(request):
    return redirect("http://" + DOMAIN + "/")
