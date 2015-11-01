#!/usr/bin/python
#
# dice roller for slack
# supports basic die rolling and new World of Darkness dice rolling
# MIT licensed as appropriate
# for latest version go to github.com/exposit/slackrollpy/
#
from random import randint
from random import seed
import time
import re
from slackclient import SlackClient
import slacktoken

# set this to false to go live and send messaging to slack
debug = True

# set this to true to output a LOT more messaging to the terminal
verbose = False

# if true, only the specified channel will be used; otherwise bot will respond on the channel the request originated on if it belongs
static_channel = False

# messaging
ready_pre_msg = "_is ready to roll._"
shutdown_msg = "_is putting away the dice."

#------------------------------------------------------------------------------------

seed()

# for logging purposes
userid = ""
token = slacktoken.token
channel = slacktoken.channel

# add up number of successes
def total_successes(results, target):
    print(target)
    x = 0
    for i in range(0, len(results)):
        if results[i] >= target:
            x = x + 1
        
    return x
  
# format results based on format list  
def format_results(numbers, formats):
    
    final_results = ""
    
    for i in range(0, len(numbers)):
        # basic formatting
        if formats[i] == "s":
            temp = "*" + str(numbers[i]) + "*"
        elif formats[i] == "f":
            temp = "_" + str(numbers[i]) + "_"
        # explode formatting
        elif formats[i] == "es":
            temp = "[*" + str(numbers[i]) + "*]"
        elif formats[i] == "ef":
            temp = "[_" + str(numbers[i]) + "_]"
        # rote formatting
        elif formats[i] == "r":
            temp = "~" + str(numbers[i]) + "~"
        elif formats[i] == "rs":
            temp = "*" + str(numbers[i]) + "*"
        elif formats[i] == "rf":
            temp = "_" + str(numbers[i]) + "_"
        # chance formatting
        elif formats[i] == "df":
            temp = "_*" + str(numbers[i]) + "*_"
        # default formatting
        else:
            temp = str(numbers[i])
            
        final_results = final_results + temp + ", "
        
    final_results = final_results[:-2]
        
    return final_results

def basic_die_roll(sides):
    result = randint(1, sides)
    return result

def roll_controller(count, sides, target=-1, explode=-1, rote=-1, chance=-1):
    
    # first clear the results list
    results_list = []
    format_list = []
    
    for i in range(0, count):
        # now roll a die
        result = basic_die_roll(sides)
        results_list.append(result)
        
        # check here for success; target = -1 (off) or num
        if target == -1:
            format_list.append("p")
        elif result >= target:
            format_list.append("s")
        elif chance == 1 and result == 1:
            format_list.append("df")
        else:
            # rote will either be -1 (off) or 1 (on)
            if rote != -1 and result < target:
                format_list.append("r")
                # now reroll a failure once, since rote is active
                rote_reroll_result = basic_die_roll(sides)
                results_list.append(rote_reroll_result)
                if rote_reroll_result >= target:
                    format_list.append("rs")
                else:
                    format_list.append("rf")
            else:
                format_list.append("f")
    
        # explode will either be a number to match or -1, with -1 being "off"
        while result >= explode and explode != -1:
            result = basic_die_roll(sides)
            results_list.append(result)
            if target == -1:
                format_list.append("ep")
            elif result >= target:
                format_list.append("es")
            else:
                format_list.append("ef")
                
    # redirect this to a text log eventually; for now, rely on slack's search
    if verbose:
        print(results_list)
        print(format_list)
    
    message = format_results(results_list, format_list)
    if target != -1:
        successes = total_successes(results_list, target)
    else:
        successes = -9
    
    return message, successes

# check for input from slack to the program
def check_for_input():
    
    global channel
    global userid
    
    test = sc.rtm_read()
    
    if len(test) > 0:
        elem = test[0]
        if verbose:
            print('RAW Message:\n%s' % test)
        if "type" in elem.keys() and "channel" in elem.keys():
            if not static_channel:
                channel = elem["channel"]
            if not "subtype" in elem.keys():    
                if elem["type"] == "message" and elem["channel"] == channel:
                    if elem["text"].startswith("roll") or elem["text"].startswith("nwod") or elem["text"] == "chance":
                        userid = elem["user"]
                        return elem["text"]
                        
    return False

# parse command for meaningful data                    
def command_received(command):
    
    if verbose:
        print("parsing command for meaningful data")
        
    # check if help needed; either plain "roll" or "roll help"
    if "help" in command or command == "roll":
        help1 = "The basic keyword is *roll XdS* with X being the number of dice to roll and S being the sides, eg, _roll 3d6_ will roll three 6 sided dice. You can also choose to *explode num* (or *e num*) to reroll if a die is that number of higher (ie, for 9-again, use _explode 9_). Use *target num* (or *t num*) to set a target (default none). Keywords: use *rote* to reroll all failed dice once (must also specify target with *target num*)."
        help2 = "\n\nNWOD: Using *nwod* in place of *roll* will set all parameters to a basic New World of Darkness roll; _nwod 7_ will roll a standard 10-again, 7 dice pool against difficulty 8. To override, simply add additional parameters, ie, _nwod 7 e8_ for 8-again. To roll a chance roll, type *chance* or *roll chance*."
        help3 = "\n\nExamples:\nroll 7d10 explode 10 target 8 _is the same as_ roll 7d10e10t8 _is the same as_ nwod 7\n nwod 7 rote _is the same as_ roll 7d10e10t8 rote"
        return help1 + " " + help2 + " " + help3, -7
            
    # now consolidate down the string
    command = command.replace("roll","")
    command = command.replace(" ", "")

    # this is a chance roll
    if "chance" in command:
        chance = 1
    else:
        chance = -1
    
    # handle using nwod defaults if choices not specified
    if "nwod" in command or "chance" in command:
        nwod = 1
        command = command.replace("nwod"," ")
    else:
        nwod = -1
    
    # is rote present? this only works later if a target is also set
    if "rote" in command:
        rote = "1"
        command = command.replace("rote", "")
    else:
        rote = -1
    
    # is there a valid count?
    if chance != -1:
        count = ["1"]
    elif nwod != -1:
        regex = re.compile(' ([0-9]*)')
        count = regex.findall(command)
    else:
        regex = re.compile('([0-9]*)d[0-9]')
        count = regex.findall(command)
        
    try:
        count = int(count[0])
    except:
        error = -1
        err_msg = "No count found, need help? Use *roll help* or try *roll 3d10*."
        return err_msg, error
    
    if count == 0:
        count = 1
    
    # are sides specified properly?
    regex = re.compile('[0-9]d([0-9]*)')
    sides = regex.findall(command)
    try:
        sides = int(sides[0])
    except:
        if nwod != -1:
            # this is nwod default
            sides = 10
        else:
            error = -2
            err_msg = "No number of sides found, need help? Use *roll help* or try *roll 3d10*."
            return err_msg, error
            
    if sides == 0:
        error = -2
        err_msg = "No number of sides found, need help? Use *roll help* or try *roll 3d10*."
        return err_msg, error
    
    # should we explode dice?
    regex = re.compile('[0-9]e(xplode)?([0-9]*)')
    explode = regex.findall(command)
    try:
        explode = [explode[0][1]]
        explode = int(explode[0])
    except:
        if nwod != -1:
            # this is nwod default
            explode = 10
        else:
            explode = -1
    
    # is there a target for success set?
    regex = re.compile('[0-9]t(arget)?([0-9]*)')
    target = regex.findall(command)
    try:
        target = [target[0][1]]
        target = int(target[0])
    except:
        if nwod != -1:
            # this is nwod default or chance
            if chance != -1:
                target = 10
            else:
                target = 8
        else:
            target = -1
        
    # and pass them to our dice rolling function
    message, successes = roll_controller(count, sides, target, explode, rote, chance)
    return message, successes

if debug:
    # msg, rc = command_received("roll 3d10 explode 10 target 8 rote")
    msg, rc = command_received("chance")
    print(msg, rc)

    quit()

# this runs until the bot is given a command it recognizes as a roll
def holding_loop():
    
    valid_command = False
    valid_command = check_for_input()
    
    if verbose:
        print(valid_command)
    
    if valid_command:
        
        message, rc = command_received(valid_command)

        tail = ""
        user = ""
        
        # -1 to -5 are reserved for errors; -6 to -9 indicate messaging; positive rcs are equal to number of successes
        if rc < 0 and rc > -5:
            tail = " [ErrCode: " + str(rc) + "]"
        elif rc == -7:
            print("[Code -7] Help request issued.")
        elif rc == -9:
            print("[Code -9] No target set so no successes reported.")
            user = "<@" + userid + "> rolled: "
        else:
            tail = " (" + str(rc) + " Successes"
            user = "<@" + userid + "> rolled: "
            tag = ")"
            if rc >= 5:
                tag = "-- EXCEPTIONAL!)"
            tail = tail + tag
        
        msg = user + message + tail

        if not debug:
            sc.rtm_send_message(channel, msg)
        print(msg)
                
    time.sleep(2)
    holding_loop()
    

# this is the core routine
sc = SlackClient(token)
if sc.rtm_connect():

    #print sc.api_call("api.test")
    #print sc.server.channels.find("general")
    
    print('\n[Status] ' + ready_pre_msg)
    if not debug:
        sc.rtm_send_message(channel, ready_pre_msg)
        time.sleep(1)
    
    holding_loop()
    
    if not debug:
        sc.rtm_send_message(channel, shutting_down_main_msg)
    else:
        print('\n[Status] ' + shutting_down_main_msg)
    
    time.sleep(1)
        
else:

    print('\n[Status] Connection Failed, invalid token?')
