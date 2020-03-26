_property_table = {}

class Material(object):
    METAL = "metal"
    STONE = "stone"
    CONCRETE = "concrete"
    DIRT = "dirt"
    MUD = "mud"
    WOOD = "wood"
    LEATHER = "leather"
    SKIN = "skin"
    PLASTIC = "plastic"
    PAPER = "paper"
    CARDBOARD = "cardboard"
    GLASS = "glass"
    WATER = "water"
    MEAT = "meat"
    BREAD = "bread"
    CHEESE = "cheese"


class MaterialProperties(object):
    """
    Class representing all the properties of a specific material
    """
    def __init__(self, material, **kwargs):
        self.material = material
        self.smell = None
        self.taste = None

        for key in kwargs:
            if not hasattr(self, key):
                raise RuntimeError("%s instance has no attribute '%s'"
                    % (self.__class__._name__, key))

            setattr(self, key, kwargs[key])

        if self.material is None:
            raise RuntimeError("Need a material type to create a %s instance"
                % self.__class__.__name__)

        if self.smell is None:
            self.smell = 'like %s' % self.material

        if self.taste is None:
            self.taste = 'like %s' % self.material


def add_material(material, **kwargs):
    """
    Define a new material type

    :param str material: unique name to represent material type
    :param kwargs: all attributes of the MaterialProperties class can be set by name here
    """
    _property_table[material] = MaterialProperties(material, **kwargs)


def get_properties(material):
    """
    Get a MaterialProperties object by material name

    :param str material: material name

    :return: material properties
    :rtype: text_game_maker.material.material.MaterialProperties
    """
    try:
        ret = _property_table[material]
    except KeyError:
        raise RuntimeError("No such material '%s'" % material)

    return ret

def get_materials():
    """
    Return a list of all material names

    :return: list of material names
    :rtype: [str]
    """
    return _property_table.keys()


add_material(Material.METAL)
add_material(Material.STONE)
add_material(Material.DIRT)
add_material(Material.MUD)
add_material(Material.WOOD)
add_material(Material.LEATHER)
add_material(Material.SKIN, taste="salty", smell="like sweat")
add_material(Material.PLASTIC)
add_material(Material.PAPER)
add_material(Material.CARDBOARD)
add_material(Material.GLASS)
add_material(Material.WATER)
add_material(Material.MEAT)
add_material(Material.BREAD)
add_material(Material.CHEESE)
