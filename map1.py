from map_builder import MapBuilder, Item, Person, run_map

def delete_equipped(map_obj, equipped):
    del map_obj.inventory_items[equipped.name]
    map_obj.inventory_items['equipped'] = None

def zorb_speak_cb(map_obj):
    equipped = map_obj.inventory_items['equipped']
    if equipped and equipped.name == 'sausage':
        delete_equipped(map_obj, equipped)
        return "Thanks for the sausage"

    return "Give me a sausage, bitch"

def room_2_enter_cb(map_obj, src, dest):
    equipped = map_obj.inventory_items['equipped']
    if equipped and equipped.name == 'metal key':
        delete_equipped(map_obj, equipped)
        dest.locked = False
        return True
    
    return True

def main():
    builder = MapBuilder(
        "a small, windowless room",
        """a small, square, windowless room."""
    )

    builder.add_item(Item("a", "metal key", "on the floor", 25))
    builder.add_item(Item("a", "sausage", "on the floor", 5))

    builder.move_west("a moist lounge", "a heavily moistened, fully furnished room")
    builder.set_locked()
    builder.add_enter_callback(room_2_enter_cb)

    builder.add_person(
        Person(
            "Zorb the keymaster", "sitting upon a chair in the corner", zorb_speak_cb
        )
    )

    builder.move_west("a cellar", "a dark cellar")
    run_map(builder.get_map())

main()
