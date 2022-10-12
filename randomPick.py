import obspython as obs
import os.path, time
import random

# Constants
SOURCE_NAME = "source"
PATH_NAME = "path"
INITIAL_TEXT_NAME = "initial_text"
COUNTDOWN_NAME = "countdown"
SPEED_NAME = "speed"
DURATION_NAME = "duration"
HOLD_NAME = "hold"

source_name = ""
file_path = ""
last_modified = time.ctime(0)
initial_text = ""
item_list = []
index = 0

current = 0
interval = 0
duration = 0
hold_duration = 0

countdown_start = 0
countdown = 0

def script_description():
    return ""

def script_load(settings):
    sh = obs.obs_get_signal_handler()
    obs.signal_handler_connect(sh, "source_activate", source_activated)
    obs.signal_handler_connect(sh, "source_deactivate", source_deactivated)

def script_update(settings):
    global source_name
    global file_path
    global interval
    global initial_text
    global countdown_start
    global duration
    global hold_duration

    source_name = obs.obs_data_get_string(settings, SOURCE_NAME)
    file_path = obs.obs_data_get_string(settings, PATH_NAME)
    initial_text = obs.obs_data_get_string(settings, INITIAL_TEXT_NAME)
    countdown_start = obs.obs_data_get_int(settings, COUNTDOWN_NAME)
    speed_factor = obs.obs_data_get_int(settings, SPEED_NAME)
    interval = 180 - (speed_factor - 1) * 15
    duration = obs.obs_data_get_int(settings, DURATION_NAME) * 1000
    hold_duration = obs.obs_data_get_int(settings, HOLD_NAME) * 1000
    update_list()

def update_list():
    global last_modified

    if file_path == "":
        return

    last_modified = time.ctime(os.path.getmtime(file_path))
    text_file = open(file_path)
    item_list.clear()
    for line in text_file.readlines():
        line = str.strip(line)
        if line != "":
            item_list.append(line)
    text_file.close()
    shuffle_list()

def shuffle_list():
    global index

    random.shuffle(item_list)
    index = 0

def counting_down():
    global countdown

    if countdown <= 0:
        obs.remove_current_callback()
        obs.timer_add(select_from_list, interval)
        countdown = countdown_start
    else:
        set_text(str(countdown))
        countdown -= 1

def match_source(calldata):
    source = obs.calldata_source(calldata, "source")
    if source is not None:
        name = obs.obs_source_get_name(source)
        return name == source_name
    return False

def source_activated(calldata):
    global countdown

    if match_source(calldata):
        set_text(initial_text)
        countdown = countdown_start
        obs.timer_add(counting_down, 1000)

def source_deactivated(calldata):
    if match_source(calldata):
        set_text("")
        obs.timer_remove(counting_down)
        obs.timer_remove(select_from_list)
        reset()

def disable_source():
    current_scene = obs.obs_scene_from_source(obs.obs_frontend_get_current_scene())
    scene_item = obs.obs_scene_find_source(current_scene, source_name)
    obs.obs_sceneitem_set_visible(scene_item, False)
    obs.obs_scene_release(current_scene)
    obs.remove_current_callback()

def reset():
    global countdown
    global current

    countdown = countdown_start
    current = 0

def select_from_list():
    global index
    global current

    if index >= len(item_list):
        shuffle_list()
    selected = item_list[index]
    set_text(selected)
    index += 1
    current += 1
    if current * interval >= duration:
        obs.remove_current_callback()
        obs.timer_add(disable_source, hold_duration)
        reset()

def set_text(text: str):
    source = obs.obs_get_source_by_name(source_name)
    if source is not None:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)

def script_defaults(settings):
    obs.obs_data_set_default_int(settings, SPEED_NAME, 7)
    obs.obs_data_set_default_string(settings, INITIAL_TEXT_NAME, "random plushie!")
    obs.obs_data_set_default_int(settings, COUNTDOWN_NAME, 3)
    obs.obs_data_set_default_int(settings, DURATION_NAME, 10)
    obs.obs_data_set_default_int(settings, HOLD_NAME, 10)

def source_select(props, sources, prop_name: str, label: str):
    p = obs.obs_properties_add_list(props, prop_name, label,
                                    obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

def script_properties():
    props = obs.obs_properties_create()

    sources = obs.obs_enum_sources()
    source_select(props, sources, SOURCE_NAME, "Source")
    obs.obs_properties_add_path(props, PATH_NAME, "Text File", obs.OBS_PATH_FILE, "*.txt", None)
    obs.obs_properties_add_text(props, INITIAL_TEXT_NAME, "Initial Text", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, COUNTDOWN_NAME, "Start Countdown", 0, 10, 1)
    obs.obs_properties_add_int_slider(props, SPEED_NAME, "Roll Speed", 1, 10, 1)
    obs.obs_properties_add_int_slider(props, DURATION_NAME, "Roll Duration (seconds)", 1, 30, 1)
    obs.obs_properties_add_int_slider(props, HOLD_NAME, "Hold Duration (seconds)", 1, 30, 1)
    obs.source_list_release(sources)

    return props

def script_unload():
    reset()
