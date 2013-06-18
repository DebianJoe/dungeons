#!/usr/bin/python

#This file contains a rough class outline for a roguelike to be built with
#libtcod or another graphical front-end.
#Focus at the moment is on game logic, not the graphics.
#
#I have tried to focus on the main aspects but the model should evolve over 
#time. Hopefully we can mainly add additional more specialised classes. 
#Complete overhaul of the basic structure will not be easy.
#
#This file is written in python syntax and should compile, however there is no 
#sense in running it, there are too many gaps that remain to be filled :-)
#
# -Frost


# ASSUMPTIONS
#   Game consists of several levels, all in 2D

class Game():
    """
    The game class contains the logic to run the game.
    It knows about turns
    It has pointers to all the other stuff, via the Game object you can drill 
    down to all components
    It can save and load
    It keeps track of the levels and knows which is the current level
    At the moment I don't see the need for sub classes 
    """
    
    #Simple array to store Level objects
    _levels =[]
    @property
    def levels(self):
        return self._levels
    @property
    def currentLevel(self):
        return self._levels
    
    #functions (not exhaustive)
    def loadGame(self):
		return
    
    def saveGame(self):
		return
    
class Utility():
    """
    Reusable utilities and logic go here
    At the moment I don't see the need for sub classes 
    """
    #examples
    # random number generator
    # rolling a hitdie
    # debug messages


##########
# LEVELS #
##########
class Level(object):
    """
    Class representing one level.
    This is the generic version containing the shared logic that is inherited 
    by the sub classes
    """
    #store a link to the map object
    _map = None
    @property
    def map(self):
        return self._map
    
    #keep track of all the characters
    _characters = []
    @property
    def characters(self):
        return self._characters
    
    #keep track of all the items
    _items = []
    @property
    def items(self):
        return self._items
        
        
class GeneratedLevel(Level):
    """
    Class representing a randomly generated level
    Specialised logic to generate a random map.
    We may have different flavors (algorithms of these
    """

class TownLevel(Level):
    """
    Class representing a fixed town level
    Specalised class that uses a fixed map and fixed characters (for example 
    town vendors)
    """

#######
# MAP #
#######
class Map():
	"""
	Describes the 2D layout of a level
	Contains logic to calculate distance, intersection, field of view, ...
	
	"""

class Room():
	"""
	Describes a rectangular section of a map, more of an utility class
	"""

##############
# CHARACTERS #
##############
class Character(object):
	"""
	Base class for characters that can move around and interact
	Should probably not be instatiated but describes the general interface of 
	a character
	Basic logic is in here, more specialised logic will be in the subclasses
	Every character has an AI that governs it
	Every character manages an inventory of items
	"""
    #keep track of inventory
    _inventory = []
    @property
    def inventory(self):
        return self._inventory
        
class Player(Character):
	"""
	Sub class representing a player
	"""

class NPC(Character):
	"""
	Sub class representing a NPC, for example a vendor
	Probably we'll need to override some inventory concepts
	"""	

class Monster(Character):
	"""
	Sub class representing a monster
	Later we can consider more specialised subclasses 
	for example Humanoid, Undead, Animal
	"""
				
#########
# ITEMS #
#########
class Item(object):
	"""
	Base class for items
	Should probably not be instatiated but describes the general interface of 
	an item
	"""

class Equipment(Item):
	"""
	Sub class for equipment = items that can be equiped
	Might need more subclasses for weapons versus armor
	"""

class Consumable(Item):
	"""
	Sub class for items that can be used.
	Not sure we might want a different class for scrolls and potions
	"""
	
class QuestItem(Item):
	"""
	Sub class for quest items
	Probably don't need this in the beginning but it would fit in here :)
	"""

######
# AI #
######
TODO Every AI governs a characters













    
if __name__ == '__main__':
    print("There is not much sense in running this file.")
