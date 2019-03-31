import sys
import os
import time
import re
import logging

from slackclient import SlackClient

from text_game_maker.utils.runner import run_map_from_filename
from text_game_maker.utils import utils

logging.basicConfig()
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])
logger.setLevel(logging.INFO)

class config(object):
    channel = None
    channel_info = None
    user_info = None
    channel_name = None
    user_name = None

    @classmethod
    def set_channel_name(cls):
        if (cls.channel_info and ('channel' in cls.channel_info)
                and ('name' in cls.channel_info['channel'])):
            cls.channel_name = cls.channel_info['channel']['name']
            return

        cls.channel_name = 'unknown'

    @classmethod
    def set_user_name(cls):
        if (cls.user_info and ('user' in cls.user_info)
                and ('name' in cls.user_info['user'])):
            cls.user_name = cls.user_info['user']['name']
            return

        cls.user_name = 'unknown'

# URL of image to use for bot icon in chats
ICON_IMAGE_URL = 'https://cdn3.iconfinder.com/data/icons/line/36/robot_head-512.png'

# Environment variable containing slack API token for bot user
TOKEN_ENV_VAR = 'SLACK_BOT_TOKEN'

# Time to wait in between polling slack for input
RTM_READ_DELAY_SECS = 0.2

# Regex to identify mentions in a received message
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def create_slack_client():
    if TOKEN_ENV_VAR not in os.environ:
        raise RuntimeError("Please set a valid bot user token in environment "
            "variable '%s'" % TOKEN_ENV_VAR)

    return SlackClient(os.environ[TOKEN_ENV_VAR])

def parse_bot_commands(slack_events, botname):
    """
    Looks for a command directed at us. Returns the message and channel name
    (or None, None if message is not for us)

    :param slack_events: slack events returned by rtm_read()
    :botname: bot ID
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == botname:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
    Finds a direct mention (a mention that is at the beginning) in message text
    and returns the user ID which was mentioned. If there is no direct mention,
    returns None

    :param str message_text: text to check
    :return: tuple of the form ``(username, message)``, where ``username`` is \
        mentioned username, and ``message`` is the message text
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def main():
    if len(sys.argv) != 2:
        logger.error("Usage: %s <map runner file>" % sys.argv[0])
        return 1

    slack_client = create_slack_client()
    if not slack_client.rtm_connect(with_team_state=False):
        logger.error("Can't connect to slack")
        return

    botname = slack_client.api_call("auth.test")["user_id"]
    config.user_info = slack_client.api_call("users.info",
            user=botname)
    config.set_user_name()

    logger.info("%s connected" % config.user_name)

    def printfunc(text):
        if not config.channel:
            return

        if text != "":
            output_text = "```%s```" % text
        else:
            output_text = text

        logger.info("sending message to channel '%s'" % config.channel_name)
        logger.debug('"%s"' % text)

        slack_client.api_call(
            "chat.postMessage",
            channel=config.channel,
            text=output_text,
            icon_url=ICON_IMAGE_URL
        )

    def inputfunc(prompt):
        command = None
        if prompt:
            printfunc(prompt)

        # rtm_read doesn't block, need to block ourselves by sleeping
        while not command:
            command, config.channel = parse_bot_commands(slack_client.rtm_read(), botname)
            # Empty string is used to indicate default values, need to catch that
            if not command and config.channel:
                command = ""
                break

            time.sleep(RTM_READ_DELAY_SECS)

        config.channel_info = slack_client.api_call("channels.info",
                channel=config.channel)
        config.set_channel_name()

        logger.info("received input from channel '%s'" % config.channel_name)
        logger.debug('"%s"' % command)
        return command

    # Send game output to slack
    utils.set_printfunc(printfunc)

    # Block on game input from slack
    utils.set_inputfunc(inputfunc)

    # Disable audio, loading/saving states, debugging
    utils.disable_commands("load", "save", "audio", "debug next command")

    try:
        run_map_from_filename(sys.argv[1])
    except KeyboardInterrupt:
        pass

    logger.info('quitting')

if __name__ == "__main__":
    main()
