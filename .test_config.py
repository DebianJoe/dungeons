#!/usr/bin/python

# This tests dungeons.conf for syntax errors, 
# valid numbers and existing function & class names.

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

import sys
import json
import random
import ConfigParser
import dungeons

red = "\033[1;31m"
green = "\033[1;32m"
yellow = "\033[1;33m"
reset = "\033[1;m"
has_errors = False

def has_key(dic, key):
    """
    Do not call this directly.
    """

    if key in dic.keys():
        return True
    else:
        print(yellow + '\t\t"' + key + '" is not defined' + reset)
        return False

def is_string(dic, key):
    """
    Test if the key exists in dictionary.
    """
    
    global has_errors
    if not has_key(dic, key):
        has_errors = True

def is_numeric(dic, key):
    """
    Test if the key value in dictionary is a number.
    """
    
    global has_errors
    if has_key(dic, key):
        try:
            int(dic[key])
        except ValueError:
            has_errors = True
            print(yellow + '\t\t"' + key + '" is not numeric' + reset)

def has_attrib(target, dic, key):
    """
    Test if the key value in dictionary is a Class or Function in dungeons.py.
    """
    
    global has_errors
    if has_key(dic, key):
        try:
            # ignore blank entries
            name = dic[key]
            if len(name) > 1:
                getattr(target, name)
        except AttributeError:
            has_errors = True
            print(yellow + '\t\t"' + dic[key] + '" not a valid function or class' + reset)

def is_list(dic, key):
    """
    Test if the key value in dictionary is a list.
    """
    
    global has_errors
    if has_key(dic, key):
        try:
            value = json.loads(dic[key])
            if not type(value) is list:
                raise Exception('not a list type')
        except Exception, e:
            has_errors = True
            print(yellow + '\t\t"' + key + '" invalid' + reset)

def is_list_of_list(dic, key):
    """
    Test if the key value in dictionary is a list.
    """
    
    global has_errors
    if has_key(dic, key):
        try:
            value = json.loads(dic[key])
            if not type(value) is list:
                raise Exception('not a list type')
            if len(value) == 0:
                raise Exception('empty list')
            if not type(value[0]) is list:
                raise Exception('must be a list of lists')
            if len(value[0]) < 2:
                raise Exception('need at least two values in the list')
        except Exception, e:
            has_errors = True
            print(yellow + '\t\t"' + key + '" invalid - ' + str(e) + reset)

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    try:
        print('\nChecking dungeons.conf')
        config.read('dungeons.conf')
    except Exception, e:
        print(red + str(e) + reset)
        sys.exit(1)
    
    for monster_name in config.get('lists', 'monster list').split(', '):
        monster = dict(config.items(monster_name))
        print('* testing %s...' % monster_name)

        # TEST MONSTER HERE
        is_string(monster, 'char')
        is_list_of_list(monster, 'chance')
        is_list(monster, 'color')
        is_numeric(monster, 'hp')
        is_numeric(monster, 'defense')
        is_numeric(monster, 'power')
        is_numeric(monster, 'xp')
        has_attrib(dungeons, monster, 'death_function')
        has_attrib(dungeons, monster, 'ai_component')
    
    for item_name in config.get('lists', 'item list').split(', '):
        item = dict(config.items(item_name))
        print('* testing %s...' % item_name)
        
        # TEST ITEM HERE
        is_list_of_list(item, 'chance')
    
    if has_errors:
        print(red + '\nUnit test failed :(' + reset)
    else:
        print(green + '\n' + random.choice(("all systems go :)",
            "ready to rock \'n roll :)", "all tests passed :)")) + reset)
