import sys
import os
import text_game_maker

def _do_quit(player, word, name):
    ret = text_game_maker.ask_yes_no("really stop playing?")
    if ret < 0:
        return
    elif ret:
        sys.exit()

def _do_show_command_list(player, word, setting):
    print text_game_maker.get_full_controls(player.fsm)

def _do_help(player, word, setting):
    if not setting or setting == "":
        print text_game_maker.basic_controls
    else:
        i, cmd = text_game_maker.run_fsm(player.fsm, setting)
        if cmd:
            print cmd.help_text().rstrip('\n')

def _move_direction(player, word, direction):
    if 'north'.startswith(direction):
        player._move_north(word)
    elif 'south'.startswith(direction):
        player._move_south(word)
    elif 'east'.startswith(direction):
        player._move_east(word)
    elif 'west'.startswith(direction):
        player._move_west(word)
    else:
        return False

    return True

def _do_move(player, word, direction):
    if not direction or direction == "":
        text_game_maker._wrap_print("Where do you want to go?")
        return

    if direction.startswith('to '):
        direction = direction[3:]

    if _move_direction(player, word, direction):
        return

    for tile in player.current.iterate_directions():
        if tile and (direction in tile.name):
            if _move_direction(player, word, player.current.direction_to(tile)):
                return

    text_game_maker._wrap_print("Don't know how to %s %s." % (word, direction))

def _do_craft(player, word, item):
    if not item or item == "":
        text_game_maker.game_print("What do you want to %s?" % word)
        helptext = text_game_maker.crafting.help_text()
        if helptext:
            text_game_maker._wrap_print(helptext)

        return

    if not player.inventory:
        text_game_maker.save_sound(text_game_maker.audio.FAILURE_SOUND)
        text_game_maker.game_print("No bag to hold items. "
                "Nothing to craft with.")
        return

    text_game_maker.crafting.craft(item, word, player.inventory)

def _get_next_unused_save_id(save_dir):
    default_num = 1
    nums = [int(x.split('_')[2]) for x in os.listdir(save_dir)]

    while default_num in nums:
        default_num += 1

    return default_num

def _get_save_dir():
    return os.path.join(os.path.expanduser("~"), '.text_game_maker_saves')

def _get_save_files():
    ret = []
    save_dir = _get_save_dir()

    if os.path.exists(save_dir):
        ret = [os.path.join(save_dir, x) for x in os.listdir(save_dir)]

    return ret

def _do_save(player, word, setting):
    filename = None
    save_dir = _get_save_dir()

    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                text_game_maker._wrap_print("Error (%d) creating directory %s"
                    % (e.errno, save_dir))
                return

    if player.loaded_file:
        ret = text_game_maker.ask_yes_no("overwrite file %s?"
            % os.path.basename(player.loaded_file))
        if ret < 0:
            return

    if player.loaded_file and ret:
        filename = player.loaded_file
    else:
        save_id = _get_next_unused_save_id(save_dir)
        default_name = "save_state_%03d" % save_id

        ret = text_game_maker.read_line_raw("Enter name to use for save file",
            cancel_word="cancel", default=default_name)

        if ret is None:
            return

        filename = os.path.join(save_dir, ret)

    player.save_state(filename)
    text_game_maker.game_print("Game state saved in %s." % filename)

def _do_load(player, word, setting):
    filename = None

    ret = _get_save_files()
    if ret:
        files = [os.path.basename(x) for x in ret]
        files.sort()
        files.append("None of these (let me enter a path to a save file)")

        index = text_game_maker.ask_multiple_choice(files,
            "Which save file would you like to load?")

        if index < 0:
            return False

        if index < (len(files) - 1):
            filename = os.path.join(_get_save_dir(), files[index])
    else:
        text_game_maker._wrap_print("No save files found. Put save files in "
            "%s, otherwise you can enter the full path to an alternate save "
            "file." % _get_save_dir())
        ret = text_game_maker.ask_yes_no("Enter path to alternate save file?")
        if ret <= 0:
            return False

    if filename is None:
        while True:
            filename = text_game_maker.read_line("Enter name of file to load",
                cancel_word="cancel")
            if filename is None:
                return False
            elif os.path.exists(filename):
                break
            else:
                text_game_maker._wrap_print("%s: no such file" % filename)

    player.load_from_file = filename
    text_game_maker._wrap_print("Loading game state from file %s."
        % player.load_from_file)
    return True
