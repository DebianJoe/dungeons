#!/usr/bin/python
#
# Project Roguelike based on libtcod's tutorials
# Special thanks to Joao F. Henriques (a.k.a. Jotaf)
# and the Guys at the libtcod forums for their work on
# libtcod and the release for a python-based RL that
# our freely available to everyone group class could use
# as a modding project.  With their work on free
# information, we can continue to openly share ideas
# and knowledge. -joe

#   Copyright (C) 2013  Joe Brock

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# The Crunchbang (#!) Python Group consists of
# DebianJoe
# kbmonkey (wesley)
# FrostLock

import libtcodpy as libtcod
import json
import ConfigParser
import math
import textwrap
import shelve

#actual size of the window
SCREEN_WIDTH = 85
SCREEN_HEIGHT = 50

#size of the map
MAP_WIDTH = 85
MAP_HEIGHT = 43

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

#spell values
HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25
GRENADE_DAMAGE = 9000

#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 10

LIMIT_FPS = 20  #20 frames-per-second maximum

# game messages
TARGET_MESSAGE = 'Target an enemy for %s with the mouse or keypad.'

color_dark_wall = libtcod.Color(130, 110, 50) * libtcod.dark_grey * 0.4
color_dark_wall2 = libtcod.light_orange * libtcod.dark_grey * 0.2
color_dark_wall3 = libtcod.chartreuse * libtcod.dark_grey * 0.2
color_light_wall = libtcod.Color(130, 110, 50)
color_light_wall2 = libtcod.light_orange * 0.3
color_light_wall3 = libtcod.light_chartreuse * 0.3

color_dark_ground = libtcod.Color(200, 180, 50) * libtcod.dark_grey * 0.5
color_dark_ground2 = libtcod.orange * 0.4
color_dark_ground3 = libtcod.chartreuse * 0.4
color_light_ground = libtcod.Color(200, 180, 50)
color_light_ground2 = libtcod.orange * 0.9
color_light_ground3 = libtcod.chartreuse * 0.9

class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        #all tiles start unexplored
        self.explored = False

        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Object(object):
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, always_visible=False, fighter=None, ai=None, item=None, equipment=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible
        self.fighter = fighter
        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self

        self.item = item
        if self.item:  #let the Item component know who owns it
            self.item.owner = self

        self.equipment = equipment
        if self.equipment:  #let the Equipment component know who owns it
            self.equipment.owner = self

            #there must be an Item component for the Equipment component to work properly
            self.item = Item()
            self.item.owner = self

    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def send_to_back(self):
        #make this object be drawn first, so all others appear above it if they're in the same tile.
        global objects
        objects.remove(self)
        objects.insert(0, self)

    def draw(self):
        #only show if it's visible to the player; or it's set to "always visible" and on an explored tile
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or
                (self.always_visible and map[self.x][self.y].explored)):
            #set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Fighter:
    #combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, xp, death_function=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.death_function = death_function

    @property
    def power(self):  #return actual power, by summing up the bonuses from all equipped items
        bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
        return self.base_power + bonus

    @property
    def defense(self):  #return actual defense, by summing up the bonuses from all equipped items
        bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
        return self.base_defense + bonus

    @property
    def max_hp(self):  #return actual max_hp, by summing up the bonuses from all equipped items
        bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus

    def attack(self, target):
        #a simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            #make the target take some damage
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage,self)
        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

    def take_damage(self, damage, attacker):
        global killerrabbit_death, wearing_amulet
        # are we immune from rabbits?
        if attacker.owner.name == 'killerrabbit' and wearing_amulet:
            message('The Amulet of the Flying Circus protects you!')
            return
        #apply damage if possible
        if damage > 0:
            self.hp -= damage

            #check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner,attacker)

    def heal(self, amount):
        #heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

class BasicMonster:
    #AI for a basic monster.
    def take_turn(self):
        #a basic monster takes its turn. if you can see it, it can see you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            #move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            #close enough, attack! (if the player is still alive.)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

class ConfusedMonster:
    #AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:  #still confused...
            #move in a random direction, and decrease the number of turns confused
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1

        else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)

class Item:
    #an item that can be picked up and used.
    def __init__(self, use_function=None, stackable=False):
        self.use_function = use_function
        self.stackable = stackable
        self.stack = [self]

    def stacksize(self):
        return len(self.stack)

    def pick_up(self):
        #add to the player's inventory and remove from the map
        if self.stackable:
            #check for existing stack
            existingindex = inventory_find(self.owner.name)
            if existingindex == -1:
                #No stack found, check if there is room in inventory to begin a new stack
                if len(inventory) >= 26:
                    message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
                else:
                    #create a new stack
                    inventory.append(self.owner)
                    objects.remove(self.owner)
                    message('You picked up a ' + self.owner.name + '!', libtcod.green)
            else:
                #add to existing stack
                existing_stack = inventory[existingindex]
                existing_stack.item.stack.append(self.owner)
                objects.remove(self.owner)
                message('You now have ' + str(existing_stack.item.stacksize()) + ' ' + self.owner.name + 's!', libtcod.green)
        else:
            if len(inventory) >= 26:
                message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
            else:
                inventory.append(self.owner)
                objects.remove(self.owner)
                message('You picked up a ' + self.owner.name + '!', libtcod.green)

                #special case: automatically equip, if the corresponding equipment slot is unused
                equipment = self.owner.equipment
                if equipment and get_equipped_in_slot(equipment.slot) is None:
                    equipment.equip()

    def drop(self):
        #special case: if the object has the Equipment component, dequip it before dropping
        if self.owner.equipment:
            self.owner.equipment.dequip()

        if self.stackable and self.stacksize() > 1:
            #Drop 1 item of the stack
            dropobject = self.stack.pop()
            dropobject.x = player.x
            dropobject.y = player.y
            objects.append(dropobject)
            message('You dropped a ' + dropobject.name + '. (' + str(self.stacksize()) + ' remaining)', libtcod.yellow)
        else:
            #add to the map and remove from the player's inventory. also, place it at the player's coordinates
            objects.append(self.owner)
            inventory.remove(self.owner)
            self.owner.x = player.x
            self.owner.y = player.y
            message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

    def use(self):
        #special case: if the object has the Equipment component, the "use" action is to equip/dequip
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return

        #just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                if self.stackable and self.stacksize() > 1:
                    self.stack.pop()
                    message('You used a ' + self.owner.name + '. (' + str(self.stacksize()) + ' remaining)', libtcod.yellow)
                else:
                    inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason

class Equipment:
    #an object that can be equipped, yielding bonuses. automatically adds the Item component.
    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus

        self.slot = slot
        self.is_equipped = False

    def toggle_equip(self):  #toggle equip/dequip status
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()

    def equip(self):
        global wearing_amulet
        #if the slot is already being used, dequip whatever is there first
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()

        #equip object and show a message about it
        self.is_equipped = True
        message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', libtcod.light_green)
        if self.owner.name == 'Amulet of the Flying Circus':
            wearing_amulet = True

    def dequip(self):
        global wearing_amulet
        #dequip object and show a message about it
        if not self.is_equipped: return
        self.is_equipped = False
        message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.', libtcod.light_yellow)
        if self.owner.name == 'Amulet of the Flying Circus':
            wearing_amulet = False

def get_equipped_in_slot(slot):  #returns the equipment in a slot, or None if it's empty
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None

def get_all_equipped(obj):  #returns a list of equipped items
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []  #other objects have no equipment

def is_blocked(x, y):
    #first test the map tile
    if map[x][y].blocked:
        return True

    #now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

def create_room(room):
    global map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global map
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global map
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def make_map():
    #BEGIN
    #Frost: temporary hack
    #this piece needs to be removed as soon as their are stairs going
    #back up. Since monster uniqueness is now across levels it can happen
    #that the player misses the killer rabbit in a higher level.
    global monster_population
    if 'killerrabbit' in monster_population.uniques:
        monster_population.uniques.remove('killerrabbit')
    #END

    global map, objects, stairs
    #the list of objects with just the player
    objects = [player]

    #fill map with "blocked" tiles
    map = [[ Tile(True)
             for y in range(MAP_HEIGHT) ]
           for x in range(MAP_WIDTH) ]

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            #this means there are no intersections, so this room is valid

            #"paint" it to the map's tiles
            create_room(new_room)

            #add some contents to this room, such as monsters
            place_objects(new_room)

            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel

                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

    #create stairs at the center of the last room
    stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()  #so it's drawn below the monsters

# Comment Frostlock: I was planning to move these Monster* classes to a
# monsters.py file. But this proved difficult since it needs global functions
# from the main dungeons.py
# I'm still hoping to do this later once we have a bit less global functions.
class Monster(Object):
    """
    Monster class representing monsters in game. Inherits from basic game
    object class.
    """
    _FLAVOR_TEXT = "Flavor text not set"
    @property
    def FlavorText(self):
        return self._FLAVOR_TEXT

    _KILLED_BY_TEXT = "Killed by text not set"
    @property
    def KilledByText(self):
        return self._KILLED_BY_TEXT

    def __init__(self, x, y, char, name, color, flavor, killed_by, fighter_comp=None, ai_comp=None):
        #Monsters are always blocking
        blocking=True
        #call constructor of super class
        super(Monster, self).__init__(x, y, char, name, color, blocks=blocking, fighter=fighter_comp, ai=ai_comp)
        #set monster specific class variables
        self._FLAVOR_TEXT = flavor
        self._KILLED_BY_TEXT = killed_by

class MonsterLibrary():
    """
    This class represents a library of monsters, basically it provides an
    interface towards the monsters config file.
    It is not aware of the game itself.
    Arguments
        config - an initialised config parser
    """

    #configparser that contains game configuration
    _CONFIG = None

    def __init__(self,config):
        self._CONFIG = config

    def createMonster(self,x,y,monster_key):
        """
        Function to build a new Monster.
        Arguments
            monster_key - string that identifies a monster in the config file.
        """
        # load the monster data from the config
        monster_data = dict(self._CONFIG.items(monster_key))

        # build the monster components
        fighter_component = Fighter(
            hp=roll_hit_die(monster_data['hitdie']),
            defense=int(monster_data['defense']),
            power=int(monster_data['power']),
            xp=int(monster_data['xp']),
            death_function=globals().get(monster_data['death_function'], None))
            #death_function=monster_data['death_function'])

        # this gets a class object by name
        ai_class = globals().get(monster_data['ai_component'])
        #ai_component=monster_data['ai_component']

        # and this instanstiates it if not None
        ai_component = ai_class and ai_class() or None

        # finally we assemble the monster object
        monster = Monster(x, y, monster_data['char'], monster_key,
            libtcod.Color(*tuple(json.loads(monster_data['color']))),
            monster_data['flavor'], monster_data['killed_by'],
            fighter_comp=fighter_component, ai_comp=ai_component)
        return monster


class MonsterPopulation():
    """
    This class represents and manages all the monsters in the game.
    It is linked to a specific game.
    Arguments
        config - an initialised config parser (received from game)
    """
    #configparser that contains game configuration
    _CONFIG = None

    #reference to a monster library on which this population is based
    _LIBRARY = None
    @property
    def library(self):
        return self._LIBRARY

    #Keep track of unique monsters
    _UNIQUES = None
    @property
    def uniques(self):
        return self._UNIQUES

    def __init__(self,config):
        self._CONFIG = config
        self._LIBRARY = MonsterLibrary(config)
        self._UNIQUES = []

    #Frost: This is double code at the moment but it is meant to be taken along
    #to a different file.
    def from_dungeon_level(self,table,dungeon_level):
        #returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
        for (value, level) in reversed(table):
            if dungeon_level >= level:
                return value
        return 0

    def place_monsters(self,room,dungeon_level):
        #maximum number of monsters per room
        max_monsters = self.from_dungeon_level([[5, 6], [3, 4], [2, 1]],dungeon_level)

        #chance of each monster
        monster_chances = {}
        for monster_name in self._CONFIG.get('lists', 'monster list').split(', '):
            chance_table = json.loads(self._CONFIG.get(monster_name, 'chance'))
            monster_chances[monster_name] = self.from_dungeon_level(chance_table,dungeon_level)

        #choose random number of monsters
        num_monsters = libtcod.random_get_int(0, 0, max_monsters)

        for i in range(num_monsters):
            #choose random spot for this monster
            x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
            y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

            #only place it if the tile is not blocked
            if not is_blocked(x, y):
                # choose a random monster
                choice = random_choice(monster_chances)

                # load the monster data from the config
                monster_data = dict(self._CONFIG.items(choice))

                # do not create multiple unique monsters
                if monster_data['unique'] == 'True':
                    if choice in self.uniques:
                        #This unique was already created, do nothing
                        continue
                    else:
                        self.uniques.append(choice)
                monster = self.library.createMonster(x,y,choice)

                objects.append(monster)

def random_choice_index(chances):  #choose one option from list of chances, returning its index
    #the dice will land on some number between 1 and the sum of the chances
    dice = libtcod.random_get_int(0, 1, sum(chances))

    #go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        #see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1

def random_choice(chances_dict):
    #choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()

    return strings[random_choice_index(chances)]

def from_dungeon_level(table):
    global dungeon_level
    #returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0

def roll_hit_die(hitdie):
    """
    this function simulates rolling hit dies and returns the resulting
    nbr of hitpoints. Hit dies are specified in the format xdy where
    x indicates the number of times that a die (d) with y sides is
    thrown. For example 2d6 means rolling 2 six sided dices.
    Arguments
        hitdie - a string in hitdie format
    Returns
        integer number of hitpoints
    """
    #interpret the hitdie string
    d_index = hitdie.lower().index('d')
    nbr_of_rolls = int(hitdie[0:d_index])
    dice_size = int(hitdie[d_index + 1:])
    #roll the dice
    role_count = 0
    hitpoints = 0
    while role_count <= nbr_of_rolls:
        role_count += 1
        hitpoints += libtcod.random_get_int(0, 1, dice_size)
    return hitpoints

def place_objects(room):
    """
    This function will place items and monsters in a room.
    """
    # Frostlock: I moved code related to monster creation out to specialised
    # classes, the logic hasn't changed much yet but this provides a place
    # for more complex monster creation logic later.

    # Leverage MonsterPopulation to place the monsters
    monster_population.place_monsters(room, dungeon_level)

    #maximum number of items per room
    max_items = from_dungeon_level([[1, 1], [2, 4]])

    #chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    for item_name in config.get('lists', 'item list').split(', '):
        chance_table = json.loads(config.get(item_name, 'chance'))
        item_chances[item_name] = from_dungeon_level(chance_table)

    #choose random number of items
    num_items = libtcod.random_get_int(0, 0, max_items)

    for i in range(num_items):
        #choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            if choice == 'heal':
                #create a healing potion
                item_component = Item(use_function=cast_heal,stackable=True)
                item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)

            elif choice == 'lightning':
                #create a lightning bolt scroll
                item_component = Item(use_function=cast_lightning,stackable=True)
                item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)

            elif choice == 'fireball':
                #create a fireball scroll
                item_component = Item(use_function=cast_fireball,stackable=True)
                item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, item=item_component)

            elif choice == 'confuse':
                #create a confuse scroll
                item_component = Item(use_function=cast_confuse,stackable=True)
                item = Object(x, y, '#', 'scroll of confusion', libtcod.light_yellow, item=item_component)

            elif choice == 'sword':
                #create a sword
                equipment_component = Equipment(slot='right hand', power_bonus=3)
                item = Object(x, y, '/', 'sword', libtcod.sky, equipment=equipment_component)

            elif choice == 'shield':
                #create a shield
                equipment_component = Equipment(slot='left hand', defense_bonus=1)
                item = Object(x, y, '[', 'shield', libtcod.darker_orange, equipment=equipment_component)

            elif choice == 'cloak':
                #create a cloak
                equipment_component = Equipment(slot='back', max_hp_bonus=10)
                item = Object(x, y, ')', 'cloak', libtcod.darker_green, equipment=equipment_component)

            elif choice == 'holy hand grenade':
                #create a holy hand grenade
                item_component = Item(use_function=cast_grenade, stackable=False)
                item = Object(x, y, 'O', 'Holy Hand Grenade', libtcod.darkest_grey, item=item_component)

            elif choice == 'Amulet of the flying circus':
                #create an Amulet of the flying circus
                equipment_component = Equipment(slot='neck', max_hp_bonus=0)
                item = Object(x, y, '"', 'Amulet of the Flying Circus', libtcod.darker_amber, equipment=equipment_component)

            objects.append(item)
            item.send_to_back()  #items appear below other objects
            item.always_visible = True  #items are visible even out-of-FOV, if in an explored area

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    #render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    #now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    #finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
                                 name + ': ' + str(value) + '/' + str(maximum))

def get_names_under_mouse():
    global mouse
    #return a string with the names of all objects under the mouse

    (x, y) = (mouse.cx, mouse.cy)

    #create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

    names = ', '.join(names)  #join the names, separated by commas
    return names.capitalize()

def render_all():
    global fov_map, color_dark_wall, color_dark_wall2,  color_light_wall
    global color_dark_ground, color_light_ground, color_light_wall2, color_dark_ground2
    global color_light_ground2
    global fov_recompute, dungeon_level
    global killerrabbit_death

    if fov_recompute:
        #recompute FOV if needed (the player moved or something)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

        #go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                if not visible:
                    #if it's not visible right now, the player can only see it if it's explored
                    if map[x][y].explored:
                        if wall and dungeon_level % 2 == 0:
                            libtcod.console_set_char_background(
                            con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        elif wall and dungeon_level % 3 == 0:
                            libtcod.console_set_char_background(
                            con, x, y, color_dark_wall3, libtcod.BKGND_SET)
                        elif wall:
                            libtcod.console_set_char_background(
                            con, x, y, color_dark_wall2, libtcod.BKGND_SET)
                        elif dungeon_level % 2 == 0:
                            libtcod.console_set_char_background(
                            con, x, y, color_dark_ground, libtcod.BKGND_SET)
                        elif dungeon_level % 3 == 0:
                            libtcod.console_set_char_background(
                            con, x, y, color_dark_ground3, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(
                            con, x, y, color_dark_ground2, libtcod.BKGND_SET)
                else:
                    #it's visible
                    if wall and dungeon_level % 2 == 0:
                        libtcod.console_set_char_background(
                        con, x, y, color_light_wall, libtcod.BKGND_SET )
                    elif wall and dungeon_level % 3 == 0:
                        libtcod.console_set_char_background(
                        con, x, y, color_light_wall3, libtcod.BKGND_SET )
                    elif wall:
                        libtcod.console_set_char_background(
                        con, x, y, color_light_wall2, libtcod.BKGND_SET )
                    elif dungeon_level % 2 == 0:
                        libtcod.console_set_char_background(
                        con, x, y, color_light_ground, libtcod.BKGND_SET )
                    elif dungeon_level % 3 == 0:
                        libtcod.console_set_char_background(
                        con, x, y, color_light_ground3, libtcod.BKGND_SET )
                    else:
                        libtcod.console_set_char_background(
                        con, x, y, color_light_ground2, libtcod.BKGND_SET )
                        #since it's visible, explore it
                    map[x][y].explored = True

    #draw all objects in the list, except the player. we want it to
    #always appear over all other objects! so it's drawn later.
    for object in objects:
        if object != player:
            object.draw()
    player.draw()

    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    #if killed by killerrabbit show special death screen
    if killerrabbit_death and game_state == 'dead':
        blood = libtcod.image_load('./media/killerrabbit.png')
        libtcod.image_set_key_color(blood, libtcod.black)
        libtcod.image_blit_2x(blood, con, 0, 0)

    #prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)

    #print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
        y += 1

    #show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.dark_red, libtcod.darker_gray)
    render_bar(1, 2, BAR_WIDTH, 'XP', player.fighter.xp, LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR,
               libtcod.darker_green, libtcod.darker_gray)
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(dungeon_level))

    #display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

    #blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

def message(new_msg, color = libtcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        #add the new line as a tuple, with the text and the color
        game_msgs.append( (line, color) )

def player_move_or_attack(dx, dy):
    global fov_recompute

    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    #try to find an attackable object there
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    #attack if target found, move otherwise
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True

def menu(header, options, width):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    #create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    #print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    #blit the contents of "window" to the root console
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 1.0)

    #present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)

    if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)

    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None

def inventory_menu(header):
    #show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for itemobject in inventory:
            text = itemobject.name
            #show additional information, in case of a stack of items
            if itemobject.item and itemobject.item.stackable and itemobject.item.stacksize() > 1:
                text = str(itemobject.item.stacksize()) + ' ' + text + 's'
            #show additional information, in case it's equipped
            if itemobject.equipment and itemobject.equipment.is_equipped:
                text = text + ' (on ' + itemobject.equipment.slot + ')'
            options.append(text)

    index = menu(header, options, INVENTORY_WIDTH)

    #if an item was chosen, return it
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

def inventory_find(itemname):
    #returns first index of item or -1 if the item is not found
    itemindex = -1
    for item in inventory:
        if item.name == itemname:
            itemindex = inventory.index(item)
    return itemindex

def msgbox(text, width=50):
    menu(text, [], width)  #use menu() as a sort of "message box"

def story():
    global race
    if race == 'Human':
        msgbox('You are a young adventurer who has entered THE UNDERDEEP\n\n'+
               'This cave has had many '+
               'horrible stories told about it around the campfires at night,'+
               ' but also stories of the amulet of the flying circus, which '+
               'could give great power to the wearer.'+
               '\n\nYou, being a brave explorer, grab your trusty dagger '+
               'and descend into the cave to find out what is really' +
                ' hiding in the dark shadows of the deep.\n\n'+
               'Use your wits to gather items to explore the depths of the '+
               'cave.  Be warned, though, that many perils await you.')

    elif race == 'Elf':
        msgbox('The elves of Windfall, being cursed by a terrible witch '+
               'have sent you, a young elvish warrior into the UNDERDEEP\n\n'+
               '...a cave that once belonged to the dwarves, but has since '+
               'fallen home to horrific monsters under the evil of the '+
               'the Necromancer Malfuriul the Vast One.\n\n' +
               'You pick up your trusty dagger '+
               'vowing to recover the amulet of the flying circus\n' +
               '...and return your people to their former glory.')

    elif race == 'Dwarf':
        msgbox('The UNDERDEEP, once home to the dwarvish people '+
               'has fallen under the spell of Malfuriul the Vast One\n\n'+
               'You pick up the dagger of your grandfather, Norat Longbeard '+
               ',and vow to reclaim the amulet of the flying circus to '+
               'cleanse the evil from your ancestral home.')

    elif race == 'Orc':
        msgbox('You are one of a few blood orcs that are alive in the Realm. '+
               'Blood of your ancestors runs trough your veins, '+
               'all you do is kill and want more blood. You also seek revenge.'+
               'You pick up your blood thirsty dagger and embrace anger in you.'+
               '"Mabaj bot ob armauk!".')

def handle_keys():
    global key, race, wearing_amulet

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  #exit game

    if game_state == 'playing':
        key_char = chr(key.c)
        #movement keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
        elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
        elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)
        elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
        elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)

            #vim movement keys
        elif key_char == 'h':
            player_move_or_attack(-1, 0)
        elif key_char == 'j':
            player_move_or_attack(0, 1)
        elif key_char == 'k':
            player_move_or_attack(0, -1)
        elif key_char == 'l':
            player_move_or_attack(1, 0)
        elif key_char == 'y':
            player_move_or_attack(-1, -1)
        elif key_char == 'u':
            player_move_or_attack(1, -1)
        elif key_char == 'b':
            player_move_or_attack(-1, 1)
        elif key_char == 'n':
            player_move_or_attack(1, 1)
            # the period key (".") makes the player wait one turn.
        elif key_char == '.':
            player_move_or_attack(0, 0)
        elif key.vk == libtcod.KEY_KP5:
            pass  #do nothing ie wait for the monster to come to you
        else:
            #test for other keys
            key_char = chr(key.c)

            if key_char == ',' or key_char == 'g':
                #pick up an item
                for object in objects:  #look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up()
                        if object.name == 'Amulet of the Flying Circus':
                            wearing_amulet = True
                        break

            if key_char == 'i':
                #show the inventory; if an item is selected, use it
                chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()

            if key_char == 'd':
                #show the inventory; if an item is selected, drop it
                chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()

            if key_char == 'c':
                #show character information
                level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                equipped_list = ', '.join(item.owner.name for item in get_all_equipped(player))
                equipped_list = 'Equipped: ' + str(equipped_list and equipped_list or 'bare handed')
                msgbox('Character Information\n\nLevel: ' + str(player.level) + ' ' + str(race) +
                       '\nExperience: ' + str(player.fighter.xp) +
                       '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
                       '\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense) +
                       '\n\n' + str(equipped_list), CHARACTER_SCREEN_WIDTH)

            if key_char == '?':
                msgbox('The ARROW keys move you around\n or use VIM-like bindings\n' +
                       'Press "g or ," to GET items\n' + 'Press "<" to go down stairs\n' + 'Press "c" for Character information\n' +
                       'Press "i" for your INVENTORY\nPress "d" to DROP an item\nPress "s" for the STORY\nPress "esc" to exit\n' +
                       'Press "Alt+Enter" for fullscreen\nPress "?" to see this screen at any time' +
                       '\n\nTarget enemies with the mouse or keypad.' +
                       '\nConfirm target with left-click or <Enter>.' +
                       '\nCancel target with right-click or <Esc>.')

            if key_char == 's':
                #makes call to funtion "Story"
                #which is specific to race
                story()

            if key_char == '<':
                #go down stairs, if the player is on them
                if stairs.x == player.x and stairs.y == player.y:
                    next_level()

            return 'didnt-take-turn'

def check_level_up():
    #see if the player's experience is enough to level-up
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        #it is! level up and ask to raise some stats
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)

        choice = None
        while choice == None:  #keep asking until a choice is made
            choice = menu('Level up! Choose a stat to raise:\n',
                          ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
                           'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
                           'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'], LEVEL_SCREEN_WIDTH)

        if choice == 0:
            player.fighter.base_max_hp += 20
            player.fighter.hp += 20
        elif choice == 1:
            player.fighter.base_power += 1
        elif choice == 2:
            player.fighter.base_defense += 1

def player_death(player,attacker):
    message(attacker.owner.KilledByText)
    #message('Player is killed by ' + attacker.owner.name.capitalize() + '.')
    global killerrabbit_death
    if attacker.owner.name == 'killerrabbit':
        killerrabbit_death = True

    #End the game
    global game_state
    message('You died!', libtcod.red)
    game_state = 'dead'

    #for added effect, transform the player into a corpse!
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster,attacker):
    #yield experience to the attacker
    attacker.xp += monster.fighter.xp
    message('The ' + monster.name + ' is dead! You gain ' + str(monster.fighter.xp) + ' experience points.', libtcod.orange)

    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()

def target_tile(max_range=None):
    global key, mouse
    #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
    # track the position of keyboard targeting
    target_x, target_y = (player.x, player.y)
    target_col = libtcod.console_get_char_background(con, target_x, target_y)
    while True:
        #render the screen. this erases the inventory and shows the names of objects under the mouse.
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        render_all()

        # replace the previous background
        # so that if we return it does not leave artifacts on screen
        libtcod.console_set_char_background(con, target_x, target_y,
                                        target_col, flag=libtcod.BKGND_SET)

        (x, y) = (mouse.cx, mouse.cy)

        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)  #cancel if the player right-clicked or pressed Escape

        #accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
                (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)

        if (key.vk in (libtcod.KEY_ENTER, libtcod.KEY_KPENTER) and
            libtcod.map_is_in_fov(fov_map, target_x, target_y) and
                (max_range is None or
                player.distance(target_x, target_y) <= max_range)):
            return (target_x, target_y)

        # move targeting reticule
        target_keys = {
                    libtcod.KEY_KP4: (-1, +0),
                    libtcod.KEY_KP6: (+1, +0),
                    libtcod.KEY_KP2: (+0, +1),
                    libtcod.KEY_KP8: (+0, -1),
                    libtcod.KEY_KP7: (-1, -1),
                    libtcod.KEY_KP9: (+1, -1),
                    libtcod.KEY_KP1: (-1, +1),
                    libtcod.KEY_KP3: (+1, +1),
                    'h': (-1, +0),
                    'l': (+1, +0),
                    'j': (+0, +1),
                    'k': (+0, -1),
                    'y': (-1, -1),
                    'u': (+1, -1),
                    'b': (-1, +1),
                    'n': (+1, +1),
                    }

        direction = None
        if key.vk in target_keys.keys():
            direction = target_keys[key.vk]
        elif chr(key.c) in target_keys:
            direction = target_keys[chr(key.c)]

        if direction:
            # replace the previous background
            libtcod.console_set_char_background(con, target_x, target_y,
                                            target_col, flag=libtcod.BKGND_SET)
            # move the reticule: adjust current position by target_keys offset
            target_x += direction[0]
            target_y += direction[1]
            # get the new background
            target_col = libtcod.console_get_char_background(con,
                                                    target_x, target_y)

        # draw the targeting reticule
        libtcod.console_set_char_background(con, target_x, target_y,
                                        libtcod.dark_flame, flag=libtcod.BKGND_SET)

def target_monster(max_range=None):
    #returns a clicked monster inside FOV up to a range, or None if right-clicked
    while True:
        (x, y) = target_tile(max_range)
        if x is None:  #player cancelled
            return None

        #return the first clicked monster, otherwise continue looping
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj

def closest_monster(max_range):
    #find closest enemy, up to a maximum range, and in the player's FOV
    closest_enemy = None
    closest_dist = max_range + 1  #start with (slightly more than) maximum range

    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
            #calculate distance between this object and the player
            dist = player.distance_to(object)
            if dist < closest_dist:  #it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy

def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', libtcod.red)
        return 'cancelled'

    message('Your wounds start to feel better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
    global player
    #find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:  #no enemy found within maximum range
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'

    #zap it!
    message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
            + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE,player.fighter)

def cast_fireball():
    global player
    #ask the player for a target tile to throw a fireball at
    message(TARGET_MESSAGE % 'fireball attack', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)

    for obj in objects:  #damage every fighter in range, including the player
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
            obj.fighter.take_damage(FIREBALL_DAMAGE,player.fighter)

def cast_grenade():
    global player
    #ask the player for a target tile to throw a fireball at
    message(TARGET_MESSAGE % 'the Holy Hand Grenade', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The Holy Hand Grenade demolishes everything!', libtcod.orange)

    for obj in objects:  #damage every fighter in range, excluding the player
        if obj != player:
            if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
                message('The ' + obj.name + ' vaporizes for ' + str(GRENADE_DAMAGE) + ' hit points.', libtcod.orange)
                obj.fighter.take_damage(GRENADE_DAMAGE, player.fighter)

def cast_confuse():
    #ask the player for a target to confuse
    message(TARGET_MESSAGE % 'confusion', libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'cancelled'

    #replace the monster's AI with a "confused" one; after some turns it will restore the old AI
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster  #tell the new component who owns it
    message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)

def recall_from_dungeon():
    global map, objects, player, stairs, inventory, game_msgs, game_state, dungeon_level, race
    global killerrabbit_created, killerrabbit_death
    #uses file "current" as a temp storage for the current level.
    file = shelve.open('current', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['stairs_index'] = objects.index(stairs)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['dungeon_level'] = game_state
    file['race'] = race
    file['events'] = [killerrabbit_created, killerrabbit_death]
    file.close()

def leave_town():
    global inventory
    #saves inventory to "current" before reopening all previous dungeon states
    file = shelve.open('current', 'n')
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file.close()

def back_to_dungeon():
    #open the previously saved shelve and load the game data
    global map, objects, player, stairs, inventory, game_msgs, game_state, dungeon_level, race
    global killerrabbit_created, killerrabbit_death

    file = shelve.open('current', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]  #get index of player in objects list and access it
    stairs = objects[file['stairs_index']]  #same for the stairs
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    dungeon_level = file['dungeon_level']
    race = file['race']
    killerrabbit_created, killerrabbit_death = file['events']
    file.close()

    initialize_fov()

def save_game():
    #open a new empty shelve (possibly overwriting an old one) to write the game data
    file = shelve.open('savegame', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)  #index of player in objects list
    file['stairs_index'] = objects.index(stairs)  #same for the stairs
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['dungeon_level'] = dungeon_level
    file['race'] = race
    file['events'] = [killerrabbit_death, wearing_amulet]
    file['monsterpopulation'] = monster_population
    file.close()

def load_game():
    #open the previously saved shelve and load the game data
    global map, objects, player, stairs, inventory, game_msgs, game_state, dungeon_level, race, monster_population
    global killerrabbit_death, wearing_amulet

    file = shelve.open('savegame', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]  #get index of player in objects list and access it
    stairs = objects[file['stairs_index']]  #same for the stairs
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    dungeon_level = file['dungeon_level']
    race = file['race']
    killerrabbit_death, wearing_amulet = file['events']
    monster_population = file['monsterpopulation']
    file.close()

    initialize_fov()

def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level
    global killerrabbit_death , wearing_amulet, monster_population

    #Frost# Need to get rid of this later
    global killerrabbit_death
    killerrabbit_death = False
    wearing_amulet = False

    #Create new MonsterPopulation that will be used in this game
    monster_population = MonsterPopulation(config)


    #create object representing the player
    if race == 'Dwarf':
        fighter_component = Fighter(hp=120, defense=1, power=2, xp=0, death_function=player_death)
    elif race == 'Elf':
        fighter_component = Fighter(hp=100, defense=2, power=2, xp=0, death_function=player_death)
    elif race == 'Human':
        fighter_component = Fighter(hp=100, defense=1, power=3, xp=0, death_function=player_death)
    elif race == 'Orc':
        fighter_component = Fighter(hp=110, defense=1, power=3, xp=0, death_function=player_death)

    player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)

    player.level = 1

    #generate map (at this point it's not drawn to the screen)
    dungeon_level = 1

    make_map()
    initialize_fov()

    game_state = 'playing'
    inventory = []

    #create the list of game messages and their colors, starts empty
    game_msgs = []

    #a warm welcoming message!
    message('The UNDERDEEP greets you with a cold breeze that smells of evil. (Press "?" for HELP)', libtcod.red)

    #initial equipment: a dagger
    equipment_component = Equipment(slot='right hand', power_bonus=2)
    obj = Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
    inventory.append(obj)
    equipment_component.equip()
    obj.always_visible = True


def next_level():
    #advance to the next level
    global dungeon_level
    message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
    player.fighter.heal(player.fighter.max_hp / 2)  #heal the player by 50%

    dungeon_level += 1
    message('After a rare moment of peace, you descend deeper into the heart of the dungeon...', libtcod.red)
    make_map()  #create a fresh new level!
    initialize_fov()

def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True

    #create the FOV map, according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

    libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)

def play_game():
    global key, mouse

    player_action = None

    mouse = libtcod.Mouse()
    key = libtcod.Key()
    #main loop
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        #render the screen
        render_all()

        libtcod.console_flush()

        #level up if needed
        check_level_up()

        #erase all objects at their old locations, before they move
        for object in objects:
            object.clear()

        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break

        #let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()

def main_menu():
    img = libtcod.image_load('./media/menu_background.png')

    while not libtcod.console_is_window_closed():
        #show the background image, at twice the regular console resolution
        libtcod.image_blit_2x(img, 0, 0, 0)

        #show the game's title, and some credits!
        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
                                 'Journey through the Underdeep')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER,
        'By The #! Python Group')

        #show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

        if choice == 0:  #new game
            #new_game()
            #play_game()
            race_menu()
        if choice == 1:  #load last game
            try:
                load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game()
        elif choice == 2:  #quit
            break

def race_menu():
    global race
    race_choice = None
    #Opening Menu for Character Racial Selection
    img = libtcod.image_load('./media/menu_background.png')
    libtcod.image_blit_2x(img, 0, 0, 0)
    msgbox("What is your decendancy young adventurer?\n" +
               "Press ENTER to Continue")
    libtcod.console_wait_for_keypress(True)
    libtcod.image_blit_2x(img, 0, 0, 0)
    while race_choice == None:  #keep asking until a choice is made
            race_choice = menu('Choose Your Race:\n',
                          ['Human',
                           'Elf',
                           'Dwarf',
                           'Orc'], LEVEL_SCREEN_WIDTH)
    if race_choice == 0:
        race = 'Human'
    elif race_choice == 1:
        race = 'Elf'
    elif race_choice == 2:
        race = 'Dwarf'
    elif race_choice == 3:
        race = 'Orc'
    new_game()
    play_game()

if __name__ == '__main__':
    libtcod.console_set_custom_font('./media/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Crunchbang Project', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
    panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

    config = ConfigParser.ConfigParser()
    config.read('dungeons.conf')

    main_menu()
